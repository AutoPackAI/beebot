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
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = GetProcessStatusArgs
    categories = ["Multiprocess"]

    def _run(self, pid: str) -> str:
        process = self.body.processes.get(int(pid))
        if not process:
            return f"Error: Process {pid} does not exist"

        status = process.poll()
        if status is None:
            return f"Process {pid} is running"

        stdout, stderr = process.communicate()
        output = stdout.strip()
        error = stderr.strip()

        return_code = process.returncode

        success_string = "successful" if return_code == 0 else "unsuccessful"
        return (
            f"The process has completed. Its exit code indicates it was {success_string}. Output: {output}. "
            f"{error}"
        )
