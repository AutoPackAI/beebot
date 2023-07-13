import platform
from typing import Callable, Type

from langchain.tools import StructuredTool
from pydantic import BaseModel

from beebot.body import Body
from beebot.body.pack_utils import get_module_path
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "os_info"
PACK_DESCRIPTION = "Get the current OS name and version information."


class OSInfoArgs(BaseModel):
    pass


def os_info(*args, **kwargs) -> str:
    return {"os_name": platform.system(), "os_version": platform.release()}


class OSInfoTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = os_info
    args_schema: Type[BaseModel] = Type[OSInfoArgs]
    body: Body

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class OSInfo(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = OSInfoTool
    args_schema: Type[BaseModel] = OSInfoArgs
