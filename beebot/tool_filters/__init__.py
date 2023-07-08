from typing import TYPE_CHECKING

from beebot.actuator.actuator import ActuatorOutput
from beebot.sensor.sensor import SensoryOutput
from beebot.tool_filters.list_directory import filter_list_directory_output
from beebot.tool_filters.read_file import filter_read_file_output

if TYPE_CHECKING:
    from beebot.autosphere import Autosphere
FILTERS = {
    "list_directory": filter_list_directory_output,
    "read_file": filter_read_file_output,
}


def filter_output(
    sphere: "Autosphere", sense: SensoryOutput, output: ActuatorOutput
) -> ActuatorOutput:
    tool_name = sense.tool_name
    if filter_fn := FILTERS.get(tool_name):
        new_response = filter_fn(sphere, sense, output)
        if new_response:
            output.response = new_response
    return output
