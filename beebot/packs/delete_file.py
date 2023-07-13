from typing import Callable, Type

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.body import Body
from beebot.body.pack_utils import get_module_path
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "delete_file"
PACK_DESCRIPTION = "Deletes a file from disk."


class DeleteFileArgs(BaseModel):
    filename: str = Field(..., description="The basename of the file to be deleted")


def delete_file(filename: str, *args, **kwargs) -> str:
    """The AI sucks at choosing when to delete files and because it's dangerous we almost never want to do it. So
    let's just not do it."""
    return f"{filename} deleted."


class DeleteFileTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = delete_file
    args_schema: Type[BaseModel] = Type[DeleteFileArgs]
    body: Body

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class DeleteFile(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = DeleteFileTool
    args_schema: Type[BaseModel] = DeleteFileArgs
