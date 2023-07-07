from typing import Callable, Type

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.autosphere import Autosphere
from beebot.packs.system_pack import SystemBasePack
from beebot.packs.utils import (
    get_module_path,
)

PACK_NAME = "task_complete"


class TaskCompleteArgs(BaseModel):
    reason: str = Field(..., description="The reason the task is considered complete")
    process_summary: str = Field(
        ..., description="A summary of the success and efficiency of the task"
    )
    function_summary: str = Field(
        ...,
        description="A summary of how the functions worked for you, and suggest generalizable functions that would "
        "have made this task easier.",
    )


def run_task_complete(reason: str, process_summary: str, function_summary: str):
    # TODO: Save the output somehow
    print("\n=== Task completed ===")
    print(f"- {reason}")
    print(f"- {process_summary}")
    print(f"- {function_summary}")
    exit()


PACK_DESCRIPTION = "Call this function when you have completed all of your goals. No further actions are possible after this function is called."


class TaskCompleteTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = run_task_complete
    args_schema: Type[BaseModel] = Type[TaskCompleteArgs]
    sphere: Autosphere


class TaskComplete(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = TaskCompleteTool
    args_schema: Type[BaseModel] = TaskCompleteArgs
