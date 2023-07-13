import json
import logging
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any

from langchain.schema import SystemMessage, AIMessage

from beebot.body.llm import call_llm
from beebot.models import Plan, Decision

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

    def decide(self, plan: Plan) -> Decision:
        """Take a Plan and send it to the LLM, returning it back to the Body"""
        logger.info("=== Sent to LLM ===")
        logger.info(plan.plan_text)
        logger.info("")
        logger.info(f"Functions provided: {[name for name in self.body.packs.keys()]}")

        response = call_llm(self.body, [SystemMessage(content=plan.plan_text)])
        logger.info("=== Received from LLM ===")
        logger.info(response.content)
        logger.info("")
        logger.info(f"Function Call: {json.dumps(response.additional_kwargs)}")
        logger.info("")
        return interpret_brain_output(response)

    def decide_with_retry(
        self, plan: Plan, retry_count: int = 0, previous_response: str = ""
    ) -> Decision:
        if retry_count and previous_response:
            plan = Plan(
                plan_text=plan.plan_text
                + (
                    f"\n\nWarning: You have attempted this next action in the past unsuccessfully. Please reassess your"
                    f" strategy. Your failed attempt is: {previous_response}"
                )
            )

        try:
            return self.decide(plan)
        except ValueError:
            logger.warning("Got invalid response from LLM, retrying...")
            if retry_count >= RETRY_LIMIT:
                raise ValueError(f"Got invalid response {RETRY_LIMIT} times in a row")
            return self.decide_with_retry(
                retry_count + 1, previous_response=plan.plan_text
            )


def interpret_brain_output(response: AIMessage) -> Decision:
    if function_call_kwargs := response.additional_kwargs.get("function_call"):
        tool_name, tool_args = parse_function_call_args(function_call_kwargs)

        decision = Decision(
            reasoning=response.content,
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
