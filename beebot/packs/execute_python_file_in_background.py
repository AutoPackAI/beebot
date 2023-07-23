import logging
import os
import shlex
import time

from pydantic import BaseModel, Field

from beebot.executor.background_process import BackgroundProcess
from beebot.packs.system_base_pack import SystemBasePack
from beebot.utils import restrict_path

logger = logging.getLogger(__name__)

PACK_NAME = "execute_python_file_in_background"

# IMPORTANT NOTE: This does NOT actually restrict the execution environment, it just nudges the AI to avoid doing
# those things.
PACK_DESCRIPTION = (
    "Executes a Python file in a restricted environment, prohibiting shell execution and filesystem access. Executes "
    "the code in the background or as a daemon process and returns immediately. Make sure the Python file adheres to"
    "the restrictions of the environment and is available in the specified file path. (Packages managed by Poetry.)"
)


class ExecutePythonFileInBackgroundArgs(BaseModel):
    file_path: str = Field(
        ...,
        description="Specifies the path to the Python file previously saved on disk.",
    )
    python_args: str = Field(
        description="Arguments to be passed when executing the file", default=""
    )
    daemonize: str = Field(
        description="Daemonize the process, detaching it from the current process."
    )


class ExecutePythonFileInBackground(SystemBasePack):
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = ExecutePythonFileInBackgroundArgs
    depends_on = [
        "install_python_package",
        "get_process_status",
        "list_processes",
        "kill_process",
    ]
    categories = ["Programming", "Files", "Multiprocess"]

    def _run(
        self, file_path: str, python_args: str = "", daemonize: str = "false"
    ) -> str:
        if self.body.config.restrict_code_execution:
            return "Error: Executing Python code is not allowed"

        file_path = os.path.join(self.body.config.workspace_path, file_path)
        if not os.path.exists(file_path):
            return "Error: File not found"

        abs_path = restrict_path(file_path, self.body.config.workspace_path)
        if not abs_path:
            return "Error: File not found"

        args_list = shlex.split(python_args)
        cmd = ["poetry", "run", "python", abs_path, *args_list]
        process = BackgroundProcess(body=self.body, cmd=cmd, daemonize=True)
        process.run()

        time.sleep(0.2)
        if process.poll() is not None:
            stdout, stderr = process.communicate()

            output = stdout.strip()
            error = stderr.strip()
            return (
                f"Process {process.pid} started, but failed. Output: {output}. {error}"
            )

        return (
            f"Process started. It has been assigned PID {process.pid}. Use this when calling "
            f"`get_process_status`."
        )
