import logging
import os
import shlex
import time

from pydantic import BaseModel, Field

from beebot.body.pack_utils import init_workspace_poetry
from beebot.execution.background_process import BackgroundProcess
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
    daemonize: bool = Field(
        description="Daemonize the process, detaching it from the current process.",
        default=False,
    )


class ExecutePythonFileInBackground(SystemBasePack):
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = ExecutePythonFileInBackgroundArgs
    depends_on = [
        "write_python_code",
        "install_python_package",
        "get_process_status",
        "list_processes",
        "kill_process",
    ]
    categories = ["Programming"]

    def _run(
        self, file_path: str, python_args: str = "", daemonize: bool = False
    ) -> str:
        if self.body.config.restrict_code_execution:
            return "Error: Executing Python code is not allowed"

        file_path = os.path.join(self.body.config.workspace_path, file_path)
        if not os.path.exists(file_path):
            return f"Error: File {file_path} does not exist. You must create it first."

        abs_path = restrict_path(file_path, self.body.config.workspace_path)
        if not abs_path:
            return f"Error: File {file_path} does not exist. You must create it first."

        init_workspace_poetry(self.config.workspace_path)
        args_list = shlex.split(python_args)
        cmd = ["poetry", "run", "python", abs_path, *args_list]
        process = BackgroundProcess(body=self.body, cmd=cmd, daemonize=daemonize)
        process.run()

        time.sleep(0.2)
        if process.poll() is not None:
            return f"Process {process.pid} started, but failed. Output: {process.stdout}. {process.stderr}"

        return (
            f"Process started. It has been assigned PID {process.pid}. Use this when calling "
            f"`get_process_status`."
        )

    async def _arun(self, *args, **kwargs) -> str:
        await self.body.file_manager.flush_to_directory()
        return self._run(*args, **kwargs)
