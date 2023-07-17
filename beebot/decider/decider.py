import json
import logging
from json import JSONDecodeError
from subprocess import TimeoutExpired
from typing import TYPE_CHECKING, Any

from beebot.body.llm import call_llm, LLMResponse
from beebot.body.pack_utils import functions_summary
from beebot.decider.deciding_prompt import decider_template
from beebot.models import Plan, Decision
from beebot.utils import list_files, files_documents

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)

RETRY_LIMIT = 3


class Decider:
    """
    The Decider is in charge of taking the Plan and deciding the next step
    """

    body: "Body"

    def __init__(self, body: "Body"):
        self.body = body

    def decide(self, plan: Plan, disregard_cache: bool = False) -> Decision:
        """Take a Plan and send it to the LLM, returning it back to the Body"""
        logger.info("=== Plan sent to LLM for Decision ===")
        logger.info(plan.plan_text)
        logger.info("")
        logger.info(f"Functions provided: {[name for name in self.body.packs.keys()]}")

        template = (
            decider_template()
            .format(
                plan=plan.plan_text,
                task=self.body.task,
                history=self.body.memories.compile_history(),
                functions=functions_summary(self.body),
                file_list=files_documents(list_files(self.body)),
            )
            .content
        )

        response = call_llm(self.body, template, disregard_cache=disregard_cache)
        logger.info("=== Decision received from LLM ===")
        if response:
            logger.info(response.text)
            logger.info("")

        logger.info(json.dumps(response.function_call, indent=4))
        logger.info("")
        return interpret_llm_response(response)

    def decide_with_retry(self, plan: Plan, retry_count: int = 0) -> Decision:
        if retry_count:
            plan = Plan(
                plan_text=plan.plan_text
                + (
                    "\n\nWarning: Invalid response received. Please reassess your strategy."
                )
            )

        try:
            return self.decide(plan, disregard_cache=retry_count > 0)
        except ValueError:
            logger.warning("Got invalid response from LLM, retrying...")
            if retry_count >= RETRY_LIMIT:
                raise ValueError(f"Got invalid response {RETRY_LIMIT} times in a row")
            return self.decide_with_retry(plan=plan, retry_count=retry_count + 1)


def interpret_llm_response(response: LLMResponse) -> Decision:
    if response.function_call:
        tool_name, tool_args = parse_function_call_args(response.function_call)

        decision = Decision(
            reasoning=response.text,
            tool_name=tool_name,
            tool_args=tool_args,
        )
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


TimeoutExpired
