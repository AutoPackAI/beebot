import os
import subprocess

from autopack import Pack
from pydantic import BaseModel, Field

from beebot.utils import restrict_path

# IMPORTANT NOTE: This does NOT actually restrict the execution environment, it just nudges the AI to avoid doing
# those things.
PACK_DESCRIPTION = (
    "Write Python code to a specified file. Will compile the code and check for any syntax errors. If "
    "there are no syntax errors, the code will be saved to the specified file. The function returns a "
    "string indicating the presence of any syntax errors in the code. However, it does not execute the "
    "code."
)


class WritePythonCodeArgs(BaseModel):
    file_name: str = Field(
        ...,
        description="The name of the file to be created or overwritten",
    )
    code: str = Field(
        ...,
        description="The Python code as a string.",
    )


class WritePythonCode(Pack):
    name = "write_python_code"
    description = PACK_DESCRIPTION
    args_schema = WritePythonCodeArgs
    categories = ["Programming"]
    reversible = False

    def check_file(self, file_name, code: str = "") -> str:
        file_path = os.path.join(self.config.workspace_path, file_name)

        try:
            abs_path = restrict_path(file_path, self.config.workspace_path)
            if not abs_path:
                return "Error: File not found"

            with open(file_path, "w+") as f:
                f.write(code)

            cmd = ["python", "-m", "py_compile", abs_path]
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=self.config.workspace_path,
            )
            output = "\n".join([process.stdout.strip(), process.stderr.strip()]).strip()

            if process.returncode:
                os.unlink(file_path)
                return f"Compile error: {output}."

            return f"Compiled successfully and saved to {file_name}."

        except Exception as e:
            os.unlink(file_path)
            return f"Error: {e.__class__.__name__} {e}"

    def _run(self, file_name: str, code: str = "") -> str:
        result = self.check_file(file_name, code)
        self.filesystem_manager.write_file(file_name, code)
        return result

    async def _arun(self, file_name: str, code: str = "") -> str:
        result = self.check_file(file_name, code)
        await self.filesystem_manager.awrite_file(file_name, code)
        return result
