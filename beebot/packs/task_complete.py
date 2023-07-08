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
    conclusion: str = Field(
        ..., description="Summary of your experience on completing the task."
    )
    process_summary: str = Field(..., description="Summary of the task's efficiency.")
    function_summary: str = Field(
        ...,
        description="Overview of function utilization and suggestions for improvements.",
    )
    output: str = Field(description="Any output requested at the end of the task.")


def run_task_complete(
    conclusion: str, process_summary: str, function_summary: str, output: str
):
    # TODO: Save the output somehow
    print("\n=== Task completed ===")
    print(f"- Output: {output}")
    print(f"- Conclusion: {conclusion}")
    print(f"- Process Summary: {process_summary}")
    print(f"- Function Summary: {function_summary}")
    exit()


PACK_DESCRIPTION = "Marks the task as completed with reasons and summaries."


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
