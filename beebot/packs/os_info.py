import platform

from pydantic import BaseModel

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "os_name_and_version"
PACK_DESCRIPTION = (
    "Get the name and version of the operating system you are running in."
)


class OSInfoArgs(BaseModel):
    pass


class OSInfo(SystemBasePack):
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = OSInfoArgs
    categories = ["System Info"]

    def _run(self) -> str:
        return f"OS Name {platform.system()}. OS Version: {platform.release()}."
