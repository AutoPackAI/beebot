import json
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import TYPE_CHECKING, Union, Any

from autopack.pack import Pack
from langchain.schema import AIMessage, BaseMessage, FunctionMessage

from beebot.prompting.sensor import (
    starting_prompt,
    FINISHED_MARKER,
    planning_prompt,
    remaining_prompt,
)
from beebot.prompting.summarization import summarization_prompt

if TYPE_CHECKING:
    from beebot.autosphere import Autosphere


@dataclass
class SensoryOutput:
    reasoning: str
    tool: str = "none"
    tool_args: dict = field(default_factory=dict)
    finished: bool = False


class Sensor:
    """
    A Sensor is in charge of taking sensory input, sending it to the LLM, taking the response, parsing it,
    and then returning the output, which in our case is a function call and reasoning.
    """

    sphere: "Autosphere"

    def __init__(self, sphere: "Autosphere"):
        self.sphere = sphere

    def start(self):
        message = starting_prompt().format(task=self.sphere.task)
        response = self.call_llm(message)

        return self.generate_sensory_output(response)

    def sense(self) -> Union[SensoryOutput, None]:
        history, next_action_number = self.compile_history()
        planning_message = planning_prompt().format(
            history=history,
            task=self.sphere.task,
        )
        response = self.call_llm(planning_message)

        # The AI will sometimes include a function call in the planning step, sometimes not. Force it to call a function
        if (
            response
            and response.additional_kwargs
            and response.additional_kwargs.get("function_call")
        ):
            return self.generate_sensory_output(response)

        message = remaining_prompt().format(
            history=history,
            task=self.sphere.task,
            next_action_number=next_action_number,
        )
        response = self.call_llm(message)

        return self.generate_sensory_output(response)

    def call_llm(self, message: BaseMessage, retry=False) -> BaseMessage:
        formatted_tools = [
            format_pack_to_openai_function(pack) for pack in self.sphere.packs
        ]
        response = self.sphere.llm(messages=[message], functions=formatted_tools)
        self.sphere.memory.chat_memory.add_message(response)
        return response

    def compile_history(self) -> tuple[str, int]:
        history = ""
        cycle_number = 1
        messages = self.sphere.memory.chat_memory.messages

        for message in self.sphere.memory.chat_memory.messages:
            if type(message) == AIMessage:
                thoughts = message.content
                if function_call := message.additional_kwargs.get("function_call"):
                    function_call_output = json.dumps(
                        {
                            "name": function_call.get("name"),
                            "args": json.loads(function_call.get("arguments")),
                        }
                    )
                    history += f"--- Action #{cycle_number}\nPlan: {thoughts}\nAction taken: {function_call_output}\n"
                    cycle_number += 1
            elif type(message) == FunctionMessage:
                history += f"Result of action: {message.content}\n"

        if len(messages) > 3:
            message = summarization_prompt().format(
                history=history,
                task=self.sphere.task,
            )
            response = self.call_llm(message)
            self.sphere.memory.chat_memory.messages = [response]
            history = response.content

        return history, cycle_number

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
                reasoning=response.content, tool=tool_name, tool_args=parsed_tool_args
            )
        except JSONDecodeError:
            return SensoryOutput(
                reasoning=response.content,
                tool=tool_name,
                tool_args={"output": function_call.get("arguments")},
            )


def format_pack_to_openai_function(pack: Pack) -> dict[str, Any]:
    # Change this if/when other LLMs support functions
    run_args = pack.run_args
    for arg_name, arg in run_args.items():
        arg.pop("required", "")
        run_args[arg_name] = arg

    return {
        "name": pack.name,
        "description": pack.description,
        "parameters": {"type": "object", "properties": run_args},
    }
