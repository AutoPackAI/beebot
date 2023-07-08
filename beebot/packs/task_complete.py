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
    success: bool = Field(..., description="Success")
    conclusion: str = Field(
        description="Summary of your experience on completing the task.", default=""
    )
    process_summary: str = Field(
        description="Summary of the task's efficiency.", default=""
    )
    function_summary: str = Field(
        description="Overview of function utilization and suggestions for improvements.",
        default="",
    )


def run_task_complete(
    sphere: Autosphere,
    success: str,
    conclusion: str,
    process_summary: str,
    function_summary: str,
):
    sphere.state.finish()
    # TODO: Save the output somehow
    if success:
        print("\n=== Task completed ===")
    else:
        print("\n=== Task failed ===")

    print(f"- Conclusion: {conclusion}")
    print(f"- Process Summary: {process_summary}")
    print(f"- Function Summary: {function_summary}")
    exit()


PACK_DESCRIPTION = (
    "Marks the task as completed. This exits the program and should not be used to perform any other "
    "action."
)


class TaskCompleteTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = run_task_complete
    args_schema: Type[BaseModel] = Type[TaskCompleteArgs]
    sphere: Autosphere

    def _run(self, *args, **kwargs):
        return super()._run(*args, sphere=self.sphere, **kwargs)


class TaskComplete(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = TaskCompleteTool
    args_schema: Type[BaseModel] = TaskCompleteArgs
