from pydantic import BaseModel

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "list_processes"
PACK_DESCRIPTION = "Lists the actively running processes and their status."


class ListProcessesArgs(BaseModel):
    pass


class ListProcesses(SystemBasePack):
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = ListProcessesArgs
    categories = ["Multiprocess"]

    def _run(self) -> str:
        running_processes = [
            f"PID {pid}: running."
            for (pid, process) in self.body.processes.items()
            if process.poll() is None
        ]

        if running_processes:
            return " ".join(running_processes)

        return "No processes running"
