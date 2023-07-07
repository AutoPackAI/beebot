from beebot.actuator.actuator import ActuatorOutput
from beebot.tool_filters.list_directory import filter_list_directory_output
from beebot.tool_filters.read_file import filter_read_file_output

FILTERS = {
    "list_directory": filter_list_directory_output,
    "read_file": filter_read_file_output,
}


def filter_output(tool_name: str, output: ActuatorOutput) -> ActuatorOutput:
    if filter_fn := FILTERS.get(tool_name):
        new_response = filter_fn(output.response)
        if new_response:
            output.response = new_response
    return output
