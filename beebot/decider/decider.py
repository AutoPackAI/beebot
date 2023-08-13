import json
import logging
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any

from beebot.body.llm import call_llm, LLMResponse
from beebot.body.pack_utils import functions_detail_list
from beebot.decider.deciding_prompt import decider_template
from beebot.models.database_models import Decision, Oversight

if TYPE_CHECKING:
    from beebot.execution.task_execution import TaskExecution

logger = logging.getLogger(__name__)

RETRY_LIMIT = 3


class Decider:
    """
    The Decider is in charge of taking the Plan and deciding the next step
    """

    task_execution: "TaskExecution"

    def __init__(self, task_execution: "TaskExecution"):
        self.task_execution = task_execution

    async def decide(
        self, oversight: Oversight, disregard_cache: bool = False
    ) -> Decision:
        """Take a Plan and send it to the LLM, returning it back to the Body"""
        # TODO: Get from agent?
        prompt_variables = {
            "plan": oversight.modified_plan_text,
            "task": self.task_execution.instructions,
            "variables": self.task_execution.compile_variables(),
            "history": await self.task_execution.compile_history(),
            "functions": functions_detail_list(self.task_execution.packs.values()),
        }
        prompt = decider_template().format(**prompt_variables)

        response = await call_llm(
            self.task_execution.body,
            prompt,
            disregard_cache=disregard_cache,
            llm=self.task_execution.body.decider_llm,
        )

        logger.info("\n=== Decision received from LLM ===")
        if response and response.text:
            logger.info(response.text)
        logger.info(json.dumps(response.function_call, indent=4))

        return await interpret_llm_response(
            prompt_variables=prompt_variables, response=response
        )

    async def decide_with_retry(
        self, oversight: Oversight, retry_count: int = 0
    ) -> Decision:
        if retry_count:
            oversight = Oversight(
                prompt_variables=oversight.prompt_variables,
                modified_plan_text=oversight.modified_plan_text
                + (
                    "\n\nWarning: Invalid response received. Please reassess your strategy."
                ),
            )

        try:
            return await self.decide(oversight, disregard_cache=retry_count > 0)
        except ValueError:
            logger.warning("Got invalid response from LLM, retrying...")
            if retry_count >= RETRY_LIMIT:
                raise ValueError(f"Got invalid response {RETRY_LIMIT} times in a row")
            return await self.decide_with_retry(
                oversight=oversight, retry_count=retry_count + 1
            )


async def interpret_llm_response(
    prompt_variables: dict[str, str], response: LLMResponse
) -> Decision:
    if response.function_call:
        tool_name, tool_args = parse_function_call_args(response.function_call)

        decision = Decision(
            reasoning=response.text,
            tool_name=tool_name,
            tool_args=tool_args,
            prompt_variables=prompt_variables,
            response=response.text,
        )
        await decision.save()
        return decision
    else:
        raise ValueError("No decision supplied")


def parse_function_call_args(
    function_call_args: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    if not function_call_args:
        raise ValueError("No function given")

    tool_name = function_call_args.get("name")
    try:
        parsed_tool_args = json.loads(function_call_args.get("arguments"))
        return tool_name, parsed_tool_args
    except JSONDecodeError:
        return tool_name, {"output": function_call_args.get("arguments")}
