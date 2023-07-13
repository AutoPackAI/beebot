from typing import Callable, Type

import psutil
from langchain.tools import StructuredTool
from pydantic import BaseModel

from beebot.body import Body
from beebot.body.pack_utils import get_module_path
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "disk_usage"
PACK_DESCRIPTION = "Get the current OS name and version information."


class DiskUsageArgs(BaseModel):
    pass


def disk_usage(*args, **kwargs) -> str:
    # Currently we will only support root directory
    usage = psutil.disk_usage("/")
    used = round(usage.used / 1024 / 1024 / 1024, 2)
    total = round(usage.total / 1024 / 1024 / 1024, 2)
    free = round(usage.free / 1024 / 1024 / 1024, 2)

    return {
        "total": f"{total} GB",
        "used": f"{used} GB",
        "free": f"{free} GB",
        "percent": usage.percent * 100,
    }


class DiskUsageTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = disk_usage
    args_schema: Type[BaseModel] = Type[DiskUsageArgs]
    body: Body

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class DiskUsage(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = DiskUsageTool
    args_schema: Type[BaseModel] = DiskUsageArgs
