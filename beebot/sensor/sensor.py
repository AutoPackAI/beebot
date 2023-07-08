import json
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import TYPE_CHECKING, Union

from langchain.schema import AIMessage, BaseMessage

from beebot.packs.utils import (
    format_packs_to_openai_functions,
)
from beebot.prompting.sensing import (
    FINISHED_MARKER,
    execution_prompt,
    initiating_prompt,
)

if TYPE_CHECKING:
    from beebot.autosphere import Autosphere


@dataclass
class SensoryOutput:
    reasoning: str
    tool_name: str = "none"
    tool_args: dict = field(default_factory=dict)
    finished: bool = False

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

    def sense(self) -> Union[SensoryOutput, None]:
        history = self.compile_history()

        # TODO: Put this in sphere class
        documents = ""
        if self.sphere.documents:
            documents = (
                "You have these documents available that you have requested before:"
            )
            for name, document in self.sphere.documents.items():
                documents += f"\n~~~ {name}~~~\n"
                documents += document
                documents += f"\n~~~ End {name}~~~\n"

        functions_summary = ", ".join([f"{pack.name}()" for pack in self.sphere.packs])
        if history:
            execution_message = execution_prompt().format(
                documents=documents,
                functions=functions_summary,
                history=history,
                task=self.sphere.task,
            )
        else:
            execution_message = initiating_prompt().format(
                functions=functions_summary,
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

        memory_content = [
            message.content for message in self.sphere.memory.chat_memory.messages
        ]
        return "\n".join(memory_content)

    def generate_sensory_output(self, response: AIMessage) -> SensoryOutput:
        if FINISHED_MARKER in response.content:
            return SensoryOutput(reasoning=response.content, finished=True)

        function_call = response.additional_kwargs.get("function_call")
        if not function_call:
            # This is probably an error state?
            return

        tool_name = function_call.get("name")
        try:
            parsed_tool_args = json.loads(function_call.get("arguments"))
            return SensoryOutput(
                reasoning=response.content,
                tool_name=tool_name,
                tool_args=parsed_tool_args,
            )
        except JSONDecodeError:
            return SensoryOutput(
                reasoning=response.content,
                tool_name=tool_name,
                tool_args={"output": function_call.get("arguments")},
            )
