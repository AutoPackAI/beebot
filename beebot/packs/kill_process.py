from subprocess import TimeoutExpired
from typing import Type

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "kill_process"
PACK_DESCRIPTION = "Terminates the process with the given PID and returns its output"


class KillProcessArgs(BaseModel):
    pid: str = Field(..., description="The PID")


class KillProcess(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = KillProcessArgs
    categories: list[str] = ["Multiprocess"]

    def _run(self, pid: str) -> dict[str, str]:
        # TODO: Support for daemonized processes from previous runs
        process = self.body.processes.get(pid)
        if not process:
            return "Error: Process does not exist"

        status = process.poll()
        if status is not None:
            return "Process had already been killed."

        output = ""
        error = ""
        try:
            stdout, stderr = process.communicate(timeout=1)
            output = stdout.strip()
            error = stderr.strip()
        except TimeoutExpired:
            pass

        process.kill()

        return f"The process has been killed. Output: {output}. {error}"
