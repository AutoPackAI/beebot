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
    document_name = sense.tool_args["file_path"]
    sphere.documents[document_name] = output.response
    return f"The contents of this file is in the section demarcated with ~~~ {document_name} ~~~ and ~~~ End {document_name} ~~~"
