from typing import Type

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "get_process_status"
PACK_DESCRIPTION = (
    "Retrieves the status of a background process. Returns the process output if it has finished. It "
    "allows you to monitor the progress and obtain information about the execution of a process "
    "running in the background."
)


class GetProcessStatusArgs(BaseModel):
    pid: str = Field(
        ...,
        description="The unique identifier of the background process given when the process was started.",
    )


class GetProcessStatus(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = GetProcessStatusArgs

    def _run(self, pid: str) -> dict[str, str]:
        try:
            try:
                process = self.body.processes[int(pid) - 1]
            except ValueError:
                return f"Error: PID {pid} is invalid. It must be an integer between 1 and {len(pid)}."

            status = process.poll()
            if status is None:
                return {"status": "running"}

            stdout, stderr = process.communicate()
            output = stdout.strip()
            error = stderr.strip()

            return_code = process.returncode

            return {
                "status": "finished",
                "success": return_code == 0,
                "output": "\n".join([output, error]),
            }

        except IndexError:
            return {"error": "Process does not exist"}
        except Exception as e:
            return {"error": str(e)}
