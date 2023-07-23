from pydantic import BaseModel

from beebot.packs.system_base_pack import SystemBasePack
from beebot.utils import list_files

PACK_NAME = "list_files"
PACK_DESCRIPTION = "Provides a list of all accessible files."


class ListFilesArgs(BaseModel):
    pass


class ListFiles(SystemBasePack):
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = ListFilesArgs
    categories = ["Files"]

    def _run(self):
        return list_files(self.body)
