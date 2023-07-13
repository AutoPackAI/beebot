import os
from typing import Callable, Type

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.body import Body
from beebot.body.pack_utils import get_module_path
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "read_file"
PACK_DESCRIPTION = "Reads and returns the content of a specified file from the disk."


class ReadFileArgs(BaseModel):
    filename: str = Field(
        ...,
        description="The name of the file to be read.",
    )


def read_file(body: Body, filename: str) -> str:
    """Read a file from disk. If/when we do sandboxing this provides a convenient way to intervene"""
    try:
        # Just in case they give us a path
        filename = os.path.basename(filename)
        file_path = os.path.join(body.config.workspace_path, filename)
        if not os.path.exists(file_path):
            return "Error: No such file"

        with open(file_path, "r") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error: {e}"


class ReadFileTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = read_file
    args_schema: Type[BaseModel] = Type[ReadFileArgs]
    body: Body

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class ReadFile(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = ReadFileTool
    args_schema: Type[BaseModel] = ReadFileArgs
