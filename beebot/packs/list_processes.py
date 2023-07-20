from typing import Type

from pydantic import BaseModel

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "list_processes"
PACK_DESCRIPTION = "Lists the actively running processes and their status."


class ListProcessesArgs(BaseModel):
    pass


class ListProcesses(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = ListProcessesArgs
    categories: list[str] = ["Multiprocess"]

    def _run(self) -> str:
        running_processes = [
            f"PID {pid}: running."
            for (pid, process) in self.body.processes.items()
            if process.poll() is None
        ]

        if running_processes:
            return " ".join(running_processes)

        return "No processes running"
