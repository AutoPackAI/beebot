import os
import shlex
import subprocess
import time
from typing import Type

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack
from beebot.utils import restrict_path

PACK_NAME = "execute_python_file_in_background"

# IMPORTANT NOTE: This does NOT actually restrict the execution environment, it just nudges the AI to avoid doing
# those things.
PACK_DESCRIPTION = (
    "Executes a Python file in a restricted environment, prohibiting shell execution and filesystem access. The "
    "function executes the code in the background and returns immediately. You cannot retrieve output from this "
    "background process. Make sure the Python file adheres to the restrictions of the environment and is available in "
    "the specified file path."
)
DEPENDS_ON = ["get_process_status"]


class ExecutePythonFileInBackgroundArgs(BaseModel):
    file_path: str = Field(
        ...,
        description="Specifies the path to the Python file previously saved on disk.",
    )
    python_args: str = Field(
        description="Arguments to be passed when executing the file", default=""
    )


class ExecutePythonFileInBackground(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = ExecutePythonFileInBackgroundArgs
    depends_on: list[str] = DEPENDS_ON

    def _run(self, file_path: str, python_args: str = "") -> str:
        file_path = os.path.join(self.body.config.workspace_path, file_path)
        if self.body.config.restrict_code_execution:
            return "Error: Executing Python code is not allowed"
        try:
            abs_path = restrict_path(file_path, self.body.config.workspace_path)
            if not abs_path:
                return "Error: File not found"

            # TODO: Maybe we want to support passing args as well?

            args_list = shlex.split(python_args)
            cmd = ["python", abs_path, *args_list]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=self.body.config.workspace_path,
            )

            self.body.processes.append(process)
            fake_pid = len(self.body.processes)

            time.sleep(0.2)
            if process.poll() is not None:
                return f"Process started with PID {fake_pid}, but failed. Call get_process_status to get the output."

            return f"Process started. It has been assigned PID {fake_pid}. Use this when calling `get_process_status`."

        except Exception as e:
            return f"Error: {e}"
