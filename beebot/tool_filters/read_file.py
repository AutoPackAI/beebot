import json
from typing import TYPE_CHECKING

from beebot.actuator.actuator import ActuatorOutput
from beebot.sensor.sensor import Sensation

if TYPE_CHECKING:
    from beebot.autosphere import Autosphere


def filter_read_file_output(
    sphere: "Autosphere",
    sense: Sensation,
    output: ActuatorOutput,
) -> str:
    response = output.response
    if response.startswith("Error:"):
        return output.response
    else:
        return f"The contents of this file are: {json.dumps(output.response)}"
