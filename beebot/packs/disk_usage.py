from typing import Type

import psutil
from pydantic import BaseModel

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "disk_usage"
PACK_DESCRIPTION = "Get the current OS name and version information."


class DiskUsageArgs(BaseModel):
    pass


class DiskUsage(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = DiskUsageArgs

    def _run(self):
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
