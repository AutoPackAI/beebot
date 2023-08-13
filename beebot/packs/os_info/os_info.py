import platform

from autopack import Pack
from pydantic import BaseModel

PACK_DESCRIPTION = "Get the name and version of the operating system you are running in."


class OSInfoArgs(BaseModel):
    pass


class OSInfo(Pack):
    name = "os_name_and_version"
    description = PACK_DESCRIPTION
    args_schema = OSInfoArgs
    categories = ["System Info"]

    def _run(self) -> str:
        return f"OS Name {platform.system()}. OS Version: {platform.release()}."

    async def _arun(self) -> str:
        return self._run()
