from typing import Callable, Type

from langchain.tools import StructuredTool
from pydantic import BaseModel

from beebot.body import Body
from beebot.packs.system_pack import SystemBasePack
from beebot.packs.utils import get_module_path
from beebot.utils import list_files

PACK_NAME = "list_files"
PACK_DESCRIPTION = "Provides a list of all accessible files."


class ListFilesArgs(BaseModel):
    pass


class ListFilesTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = list_files
    body: Body
    args_schema: Type[BaseModel] = Type[ListFilesArgs]

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class ListFiles(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = ListFilesTool
