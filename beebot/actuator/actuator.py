import json
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any, TYPE_CHECKING

from langchain.schema import FunctionMessage

if TYPE_CHECKING:
    from beebot.autosphere import Autosphere


@dataclass
class ActuatorOutput:
    response: any = ""
    error_reason: str = ""
    success: bool = True


class Actuator:
    sphere: "Autosphere"

    def __init__(self, sphere: "Autosphere"):
        self.sphere = sphere

    def actuate(self, tool_name: str, tool_args: Any) -> ActuatorOutput:
        """Get pack from tool name. call it"""
        try:
            pack = next(pack for pack in self.sphere.packs if pack.name == tool_name)
        except StopIteration:
            return ActuatorOutput(
                success=False,
                error_reason=f"Invalid tool name received: {tool_name}. It may be invalid or may not be installed.",
            )

        result = pack.run(tool_input=tool_args)
        self.sphere.memory.chat_memory.add_message(
            FunctionMessage(name=tool_name, content=result, additional_kwargs=tool_args)
        )

        try:
            return ActuatorOutput(response=json.loads(result))
        except JSONDecodeError:
            print("JSON decode failed")

        return ActuatorOutput(response={"output": result})
