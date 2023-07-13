from typing import TYPE_CHECKING

from langchain.schema import SystemMessage

from beebot.prompting.sensing import stimulus_template
from beebot.utils import list_files

if TYPE_CHECKING:
    from beebot.body import Body


class Stimulus:
    input: SystemMessage

    def __init__(self, input_message: SystemMessage):
        self.input = input_message

    @classmethod
    def generate_stimulus(cls, body: "Body") -> "Stimulus":
        functions_summary = ", ".join([f"{name}" for name in body.packs.keys()])
        stimulus_message = stimulus_template().format(
            functions=functions_summary,
            file_list=", ".join(list_files(body)),
            plan=body.current_plan,
            task=body.initial_task,
            history=body.memories.compile_history(),
        )

        return cls(input_message=stimulus_message)
