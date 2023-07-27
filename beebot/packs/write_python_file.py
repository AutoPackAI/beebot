import os
import subprocess

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack
from beebot.utils import restrict_path

PACK_NAME = "write_python_code"

# IMPORTANT NOTE: This does NOT actually restrict the execution environment, it just nudges the AI to avoid doing
# those things.
PACK_DESCRIPTION = (
    "Write Python code to a specified file. Will compile the code and check for any syntax errors. If "
    "there are no syntax errors, the code will be saved to the specified file. The function returns a "
    "string indicating the presence of any syntax errors in the code. However, it does not execute the "
    "code."
)


class WritePythonFileArgs(BaseModel):
    file_name: str = Field(
        ...,
        description="The name of the file to be created or overwritten",
    )
    code: str = Field(
        ...,
        description="The Python code as a string.",
    )


class WritePythonFile(SystemBasePack):
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = WritePythonFileArgs
    categories = ["Programming", "Files"]
    reversible = False

    def _run(self, file_name: str, code: str = "") -> str:
        file_path = os.path.join(self.body.config.workspace_path, file_name)
        if self.body.config.restrict_code_execution:
            return "Error: Executing Python code is not allowed"

        try:
            abs_path = restrict_path(file_path, self.body.config.workspace_path)
            if not abs_path:
                return (
                    f"Error: File {file_path} does not exist. You must create it first."
                )

            with open(file_path, "w+") as f:
                f.write(code)

            cmd = ["python", "-m", "py_compile", abs_path]
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=self.body.config.workspace_path,
            )
            output = "\n".join([process.stdout.strip(), process.stderr.strip()]).strip()

            if process.returncode:
                return f"Compile error: {output}."

            return f"Compiled successfully and saved to {file_name}."

        except Exception as e:
            return f"Error: {e}"
