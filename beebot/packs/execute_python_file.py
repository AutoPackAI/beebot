import os
from typing import Type

from langchain.tools.python.tool import sanitize_input
from langchain.utilities import PythonREPL
from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "execute_python_file"

# IMPORTANT NOTE: This does NOT actually restrict the execution environment, it just nudges the AI to avoid doing
# those things.
PACK_DESCRIPTION = (
    "Executes a Python file in a restricted environment, prohibiting shell execution and filesystem access. The "
    "function executes the code in the file and returns the output of the execution as a string. Make sure the "
    "Python file adheres to the restrictions of the environment and is available in the specified file path."
)


def restrict_path(file_path: str, workspace_dir: str):
    absolute_path = os.path.abspath(file_path)
    relative_path = os.path.relpath(absolute_path, workspace_dir)

    if relative_path.startswith("..") or "/../" in relative_path:
        return None

    return absolute_path


class ExecutePythonFileArgs(BaseModel):
    file_path: str = Field(
        ...,
        description="Specifies the path to the Python file previously saved on disk.",
    )


class ExecutePythonFile(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = ExecutePythonFileArgs

    def _run(self, file_path: str) -> str:
        if self.body.config.restrict_code_execution:
            return "Error: Executing Python code is not allowed"
        try:
            abs_path = restrict_path(file_path, self.body.config.workspace_path)
            if not abs_path:
                return "Error: File not found"

            with open(abs_path, "r") as f:
                repl = PythonREPL(_globals=globals(), _locals=None)
                sanitized_code = sanitize_input(f.read())
                result = repl.run(sanitized_code)

                return f'Execution successful. Output of execution: "{result.strip()}"'

        except Exception as e:
            return f"Error: {e}"
