import json
from json import JSONDecodeError
from typing import Any, TYPE_CHECKING

from langchain.schema import AIMessage

from beebot.models import Action

if TYPE_CHECKING:
    from beebot.body import Body


class Interpreter:
    body: "Body"

    def __init__(self, body: "Body"):
        self.body = body

    def interpret_brain_output(self, response: AIMessage) -> Action:
        if function_call_kwargs := response.additional_kwargs.get("function_call"):
            tool_name, tool_args = self.parse_function_call_args(function_call_kwargs)

            action = Action(
                reasoning=response.content,
                tool_name=tool_name,
                tool_args=tool_args,
            )
            return action
        else:
            raise ValueError("No action supplied")

    @staticmethod
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
