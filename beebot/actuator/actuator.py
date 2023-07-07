import json
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from beebot.autosphere import Autosphere


@dataclass
class ActuatorOutput:
    response: any = ""
    error_reason: str = ""
    success: bool = True

    def compressed(self) -> str:
        """Return this output as a str that is smaller so that it uses fewer tokens"""
        result = self.response
        # Make dicts more readable
        if type(result) == dict:
            if self.success:
                return ", ".join([f"{k}: {v}" for (k, v) in result.items()])
            else:
                return "Error: " + ", ".join([f"{k}: {v}" for (k, v) in result.items()])
        else:
            if self.success:
                return result
            else:
                return f"Error: {result}"


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

        try:
            return ActuatorOutput(response=json.loads(result))
        except JSONDecodeError:
            return ActuatorOutput(response=result)
