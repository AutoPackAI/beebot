import platform
from typing import Type

from pydantic import BaseModel

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "os_name_and_version"
PACK_DESCRIPTION = (
    "Get the name and version of the operating system you are running in."
)


class OSInfoArgs(BaseModel):
    pass


class OSInfo(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = OSInfoArgs
    categories: list[str] = ["System Info"]

    def _run(self) -> str:
        return {"os_name": platform.system(), "os_version": platform.release()}
