import os
import subprocess
from typing import Type

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "execute_python_file_in_background"

# IMPORTANT NOTE: This does NOT actually restrict the execution environment, it just nudges the AI to avoid doing
# those things.
PACK_DESCRIPTION = (
    "Executes a Python file in a restricted environment, prohibiting shell execution and filesystem access. The "
    "function executes the code in the background and returns immediately. You cannot retrieve output from this "
    "background process. Make sure the Python file adheres to the restrictions of the environment and is available in "
    "the specified file path."
)


def restrict_path(file_path: str, workspace_dir: str):
    absolute_path = os.path.abspath(file_path)
    relative_path = os.path.relpath(absolute_path, workspace_dir)

    if relative_path.startswith("..") or "/../" in relative_path:
        return None

    return absolute_path


class ExecutePythonFileInBackgroundArgs(BaseModel):
    file_path: str = Field(
        ...,
        description="Specifies the path to the Python file previously saved on disk.",
    )


class ExecutePythonFileInBackground(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = ExecutePythonFileInBackgroundArgs

    def _run(self, file_path: str) -> str:
        file_path = os.path.join(self.body.config.workspace_path, file_path)
        if self.body.config.restrict_code_execution:
            return "Error: Executing Python code is not allowed"
        try:
            abs_path = restrict_path(file_path, self.body.config.workspace_path)
            if not abs_path:
                return "Error: File not found"

            cmd = ["python", abs_path]
            self.body.processes.append(subprocess.Popen(cmd))

            return f"Process started successfully."

        except Exception as e:
            return f"Error: {e}"
