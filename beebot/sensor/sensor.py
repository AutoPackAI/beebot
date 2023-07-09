import json
import re
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import TYPE_CHECKING, Union, Any

from jsbeautifier import beautify
from langchain.schema import AIMessage, BaseMessage

from beebot.packs.utils import (
    format_packs_to_openai_functions,
)
from beebot.prompting.sensing import (
    execution_prompt,
    initiating_prompt,
)
from beebot.utils import list_files

if TYPE_CHECKING:
    from beebot.autosphere import Autosphere


@dataclass
class Sensation:
    reasoning: str
    tool_name: str = "none"
    tool_args: dict = field(default_factory=dict)

    def compressed_dict(self):
        """Return this output as a dict that is smaller so that it uses fewer tokens"""
        return {"tool": self.tool_name, "args": self.tool_args}


class Sensor:
    """
    A Sensor is in charge of taking sensory input from a Sphere, sending it to the LLM, taking the response, parsing it,
    and then returning the output, back (which in our case is a function call and reasoning) back to the Sphere.
    """

    sphere: "Autosphere"

    def __init__(self, sphere: "Autosphere"):
        self.sphere = sphere

    def sense(self) -> Union[Sensation, None]:
        history = self.compile_history()

        functions_summary = ", ".join([f"{pack.name}" for pack in self.sphere.packs])
        if history:
            execution_message = execution_prompt().format(
                functions=functions_summary,
                file_list=list_files(self.sphere),
                history=history,
                task=self.sphere.task,
            )
        else:
            execution_message = initiating_prompt().format(
                functions=functions_summary,
                file_list=list_files(self.sphere),
                task=self.sphere.task,
            )

        self.sphere.logger.info("=== Sent to LLM ===")
        for response_line in execution_message.content.split("\n"):
            self.sphere.logger.info(response_line)
        self.sphere.logger.info("")
        self.sphere.logger.info(
            f"Functions provided: {json.dumps(format_packs_to_openai_functions(self.sphere.packs))}"
        )

        # For iterative control / command authorization:
        # import pdb

        # pdb.set_trace()
        response = self.call_llm(execution_message)
        # No matter what I try it seems to occasionally return the function call in the response and not as a proper
        # function_call. So I guess we try to parse it.
        if not response.additional_kwargs.get("function_call"):
            try:
                function_name, function_args = extract_function_call_from_response(
                    response.content
                )
                response.additional_kwargs["function_call"] = {
                    "name": function_name,
                    "arguments": function_args,
                }
            except:
                pass

        self.sphere.logger.info("=== Received from LLM ===")
        for response_line in response.content.replace("\n\n", "\n").split("\n"):
            self.sphere.logger.info(response_line)
        self.sphere.logger.info(
            f"Function call: {json.dumps(response.additional_kwargs)}"
        )
        return self.generate_sensory_output(response)

    def call_llm(self, message: BaseMessage, retry=False) -> BaseMessage:
        response = self.sphere.llm(
            messages=[message],
            functions=format_packs_to_openai_functions(self.sphere.packs),
        )
        return response

    def compile_history(self) -> str:
        if not self.sphere.memory.chat_memory.messages:
            return ""

        memory_content = []
        for message in self.sphere.memory.chat_memory.messages:
            memory_content.append(message.content)

        return "\n".join(memory_content)

    def generate_sensory_output(self, response: AIMessage) -> Sensation:
        function_call = response.additional_kwargs.get("function_call")
        if not function_call:
            # This is probably an error state?
            return

        tool_name = function_call.get("name")
        try:
            parsed_tool_args = json.loads(function_call.get("arguments"))
            return Sensation(
                reasoning=response.content,
                tool_name=tool_name,
                tool_args=parsed_tool_args,
            )
        except JSONDecodeError:
            return Sensation(
                reasoning=response.content,
                tool_name=tool_name,
                tool_args={"output": function_call.get("arguments")},
            )


def extract_function_call_from_response(content: str) -> tuple[str, dict[str, Any]]:
    """
    Sometimes the LLM will return the function call in the content instead of in the proper function_call parameter.
    No matter how I engineer the prompt it still does this.
    This is inconvenient and I hope this is eventually no longer needed, but here it is for now.
    """
    # It seems to always include it in ```typescript code blocks.
    code_block_match = re.search(r"```(?:\w+)\n(.*?)```", content, re.DOTALL)

    if code_block_match is None:
        return {}

    code_block = code_block_match.group(1)

    # Remove the language identifier if present
    code_block = re.sub(r"^\w+\n", "", code_block, flags=re.MULTILINE)

    # Extract the method name
    method_match = re.search(r"\.(\w+)\(", code_block)
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
