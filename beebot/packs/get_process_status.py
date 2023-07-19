from typing import Type

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "get_process_status"
PACK_DESCRIPTION = (
    "Retrieves the status of the background process with the given pid. Returns the process output if it has "
    "finished."
)


class GetProcessStatusArgs(BaseModel):
    pid: str = Field(..., description="The Process ID")


class GetProcessStatus(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = GetProcessStatusArgs
    categories: list[str] = ["Multiprocess"]

    def _run(self, pid: str) -> str:
        # TODO: Support for daemonized processes
        process = self.body.processes.get(pid)
        if not process:
            return f"Error: Process {pid} does not exist"

        status = process.poll()
        if status is None:
            return f"Process {pid} is active"

        stdout, stderr = process.communicate()
        output = stdout.strip()
        error = stderr.strip()

        return_code = process.returncode

        success_string = "successful" if return_code == 0 else "unsuccessful"
        return (
            f"The process has completed. Its exit code indicates it was {success_string}. Output: {output}. "
            f"{error}"
        )
