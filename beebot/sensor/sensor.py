import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union, Any

from autopack.pack import Pack
from langchain.schema import AIMessage, BaseMessage

from beebot.prompting.sensor import starting_prompt, remaining_prompt

if TYPE_CHECKING:
    from beebot.autosphere import Autosphere


@dataclass
class SensoryOutput:
    reasoning: str
    tool: str
    tool_args: dict


class Sensor:
    """
    A Sensor is in charge of taking sensory input, sending it to the LLM, taking the response, parsing it,
    and then returning the output, which in our case is a function call and reasoning.
    """

    sphere: "Autosphere"

    def __init__(self, sphere: "Autosphere"):
        self.sphere = sphere
        # type: ignore

    def start(self):
        message = starting_prompt().format(
            task=self.sphere.task,
        )
        response = self.call_llm(message)

        return self.generate_sensory_output(response)

    def sense(self) -> Union[SensoryOutput, None]:
        message = remaining_prompt().format()
        response = self.call_llm(message)

        return self.generate_sensory_output(response)

    def call_llm(self, message: BaseMessage) -> dict[str, Any]:
        formatted_tools = [
            format_pack_to_openai_function(pack) for pack in self.sphere.packs
        ]
        self.sphere.memory.chat_memory.add_message(message)
        response = self.sphere.llm(
            messages=self.sphere.memory.chat_memory.messages,
            functions=formatted_tools,
        )
        self.sphere.memory.chat_memory.add_message(response)
        return response

    def normalize_tool_args(self, tool_name: str, tool_args: str) -> Any:
        """
        Normalize tool args e.g. pulling them out of
        TODO: Figure out why this is
        """
        # TODO: Handle JSON errors

    def generate_sensory_output(self, response: AIMessage) -> SensoryOutput:
        function_call = response.additional_kwargs.get("function_call")
        if not function_call:
            # I think this means that it's done?
            return

        tool_name = function_call.get("name")
        parsed_tool_args = json.loads(function_call.get("arguments"))
        return SensoryOutput(
            reasoning=response.content, tool=tool_name, tool_args=parsed_tool_args
        )


def format_pack_to_openai_function(pack: Pack) -> dict[str, Any]:
    # Change this if/when other LLMs support functions
    return {
        "name": pack.name,
        "description": pack.description,
        "parameters": {"type": "object", "properties": pack.run_args},
    }
