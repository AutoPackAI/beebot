import json
import re
from json import JSONDecodeError
from typing import Any, TYPE_CHECKING

from jsbeautifier import beautify
from langchain.schema import AIMessage

from beebot.models import Action

if TYPE_CHECKING:
    from beebot.body import Body


class Brainstem:
    body: "Body"

    def __init__(self, body: "Body"):
        self.body = body

    def interpret_brain_output(self, response: AIMessage) -> Action:
        tool_name, tool_args = self.parse_brain_response(response)

        action = Action(
            reasoning=response.content,
            tool_name=tool_name,
            tool_args=tool_args,
        )
        return action

    def parse_brain_response(self, response: AIMessage) -> tuple[str, dict[str, Any]]:
        # No matter what I try it seems to occasionally return the function call in the response and not as a proper
        # function_call. So I guess we try to parse it.
        if function_call_kwargs := response.additional_kwargs.get("function_call"):
            return self.parse_function_call_args(function_call_kwargs)
        else:
            function_name, function_args = self.extract_function_call_from_response(
                response.content
            )
            response.additional_kwargs["function_call"] = {
                "name": function_name,
                "arguments": function_args,
            }
            return function_name, function_args

    @staticmethod
    def parse_function_call_args(
        function_call_args: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        if not function_call_args:
            # This is probably an error state?
            return None, None

        tool_name = function_call_args.get("name")
        try:
            parsed_tool_args = json.loads(function_call_args.get("arguments"))
            return tool_name, parsed_tool_args
        except JSONDecodeError:
            return tool_name, {"output": function_call_args.get("arguments")}

    @staticmethod
    def extract_function_call_from_response(content: str) -> tuple[str, dict[str, Any]]:
        """
        Sometimes the LLM will return the function call in the content instead of in the proper function_call parameter.
        No matter how I engineer the prompt it still does this.
        This is inconvenient and I hope this is eventually no longer needed, but here it is for now.
        """
        # It seems to always include it in ```typescript code blocks.
        code_block_match = re.search(r"```(?:\w+)\n(.*?)```", content, re.DOTALL)

        if code_block_match is None:
            # This fuckin thing, maybe abandon functions all together?
            return None, None

        code_block = code_block_match.group(1)

        # Remove the language identifier if present
        code_block = re.sub(r"^\w+\n", "", code_block, flags=re.MULTILINE)

        # Extract the method name
        method_match = re.search(r"\.(\w+)\(", code_block)
        if not method_match:
            import pdb

            pdb.set_trace()
            method_match = re.search(r"(\w+)\(", code_block)

        method = method_match.group(1)
        if method.startswith("function."):
            method = method.replace("function.", "")

        # Extract the arguments as a string
        arguments_str = code_block.split("(", 1)[1].rsplit(")", 1)[0]

        # The arguments can possibly come as JSON or Javascript Objects
        try:
            arguments = json.loads(arguments_str)
        except JSONDecodeError:
            try:
                arguments_str = re.sub(r"(\w+):", r'"\1":', beautify(arguments_str))
                arguments = json.loads(arguments_str)
            except JSONDecodeError:
                # Welp
                arguments = {}

        return method, arguments
