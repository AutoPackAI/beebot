import os
import shlex
import subprocess
import time
from typing import Optional

from pydantic import BaseModel, Field

from beebot.body.pack_utils import init_workspace_poetry
from beebot.packs.system_base_pack import SystemBasePack
from beebot.utils import restrict_path

PACK_NAME = "execute_python_file"

# IMPORTANT NOTE: This does NOT actually restrict the execution environment, it just nudges the AI to avoid doing
# those things.
PACK_DESCRIPTION = (
    "Executes a Python file in a restricted environment, prohibiting shell execution and filesystem access. Returns "
    "the output of the execution as a string. Ensure file adherence to restrictions and availability in the specified "
    "path. (Packages managed by Poetry.)"
)


class TimedOutSubprocess:
    """A convenience class to allow creating a subprocess with a timeout while capturing its output"""

    cmd: list[str]
    process: Optional[subprocess.Popen[str]]

    def __init__(self, cmd: list[str]) -> None:
        self.cmd = cmd
        self.process = None

    def run(self, timeout: int, **kwargs) -> None:
        self.process = subprocess.Popen(self.cmd, universal_newlines=True, **kwargs)

        start_time = time.time()
        while self.process.poll() is None:  # None means the process hasn't finished
            if time.time() - start_time > timeout:
                self.process.terminate()  # Kill the process
                break

            time.sleep(1)

        if self.process.returncode is not None and self.process.returncode != 0:
            print(f"The agent exited with return code {self.process.returncode}")

        output, error = self.process.communicate()
        return "\n".join([output.strip(), error.strip()]).strip()


class ExecutePythonFileArgs(BaseModel):
    file_path: str = Field(
        ...,
        description="Specifies the path to the Python file previously saved on disk.",
    )
    python_args: str = Field(
        description="Arguments to be passed when executing the file", default=""
    )


class ExecutePythonFile(SystemBasePack):
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = ExecutePythonFileArgs
    categories = ["Programming", "Files"]
    depends_on = ["install_python_package", "write_python_code"]

    def _run(self, file_path: str, python_args: str = "") -> str:
        file_path = os.path.join(self.body.config.workspace_path, file_path)
        if self.body.config.restrict_code_execution:
            return "Error: Executing Python code is not allowed"
        try:
            abs_path = restrict_path(file_path, self.body.config.workspace_path)
            if not abs_path:
                return (
                    f"Error: File {file_path} does not exist. You must create it first."
                )

            init_workspace_poetry(self.config.workspace_path)
            args_list = shlex.split(python_args)
            cmd = ["poetry", "run", "python", abs_path, *args_list]
            process = TimedOutSubprocess(cmd)
            process.run(
                timeout=self.body.config.process_timeout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.body.config.workspace_path,
            )
            os_subprocess = process.process
            output, error = os_subprocess.communicate()

            if os_subprocess.returncode:
                return f"Execution failed with exit code {os_subprocess.returncode}. Output: {output}. {error}"

            if output:
                return f"Execution complete. Output: {output}"

            return "Execution complete."

        except Exception as e:
            return f"Error: {e}"
