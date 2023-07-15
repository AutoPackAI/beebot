import subprocess
from typing import Type

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "execute_python_code"
PACK_DESCRIPTION = "Executes Python code in a restricted environment, prohibiting shell execution and filesystem access. Ensure that the provided Python code is safe and adheres to the restrictions of the environment."


class ExecutePythonCodeArgs(BaseModel):
    code: str = Field(
        ...,
        description="The code to be executed.",
    )


class ExecutePythonCode(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = ExecutePythonCodeArgs

    def _run(self, code: str) -> str:
        if self.body.config.restrict_code_execution:
            return "Error: Executing Python code is not allowed"
        try:
            proc = subprocess.Popen(
                ["python", "-c", code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.body.config.workspace_path,
            )
            proc.wait()
            stdout, stderr = proc.communicate()

            if proc.returncode > 0:
                return (
                    f'Exit code {proc.returncode}. Captured stderr: "{stderr.strip()}". '
                    f'Captured output: "{stdout.strip()}"'
                )
            return f'Executed successfully. Captured output: "{stdout.strip()}"'
        except Exception as e:
            return f"Error: {e}"
