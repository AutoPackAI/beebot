import os
import shlex
import subprocess
from typing import Type

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack
from beebot.utils import restrict_path

PACK_NAME = "execute_python_file"

# IMPORTANT NOTE: This does NOT actually restrict the execution environment, it just nudges the AI to avoid doing
# those things.
PACK_DESCRIPTION = (
    "Executes a Python file in a restricted environment, prohibiting shell execution and filesystem access. The "
    "function executes the code in the file and returns the output of the execution as a string. Make sure the "
    "Python file adheres to the restrictions of the environment and is available in the specified file path."
)


class ExecutePythonFileArgs(BaseModel):
    file_path: str = Field(
        ...,
        description="Specifies the path to the Python file previously saved on disk.",
    )
    python_args: str = Field(
        description="Arguments to be passed when executing the file", default=""
    )


class ExecutePythonFile(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = ExecutePythonFileArgs

    def _run(self, file_path: str, python_args: str = "") -> str:
        file_path = os.path.join(self.body.config.workspace_path, file_path)
        if self.body.config.restrict_code_execution:
            return "Error: Executing Python code is not allowed"
        try:
            abs_path = restrict_path(file_path, self.body.config.workspace_path)
            if not abs_path:
                return "Error: File not found"

            args_list = shlex.split(python_args)
            cmd = ["python", abs_path, *args_list]
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=self.body.config.workspace_path,
            )
            output = "\n".join([process.stdout.strip(), process.stderr.strip()]).strip()

            if process.returncode:
                return f"Execution failed with exit code {process.returncode}. Output: {output}"

            if output:
                return f"Execution successful. Output: {output}"

            return "Execution successful."

        except Exception as e:
            return f"Error: {e}"
