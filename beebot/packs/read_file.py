import json
import os
from typing import Callable, Type

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.autosphere import Autosphere
from beebot.packs.system_pack import SystemBasePack
from beebot.packs.utils import get_module_path

PACK_NAME = "read_file"
PACK_DESCRIPTION = "Reads and returns the content of a specified file from the disk."


class ReadFileArgs(BaseModel):
    filename: str = Field(
        ...,
        description="The name of the file to be read.",
    )


def read_file(sphere: Autosphere, filename: str):
    """Read a file from disk. If/when we do sandboxing this provides a convenient way to intervene"""
    try:
        # Just in case they give us a path
        filename = os.path.basename(filename)
        file_path = os.path.join(sphere.workspace_path, filename)
        if not os.path.exists(file_path):
            return "Error: No such file"

        with open(file_path, "r") as f:
            content = f.read()
        return f"Contents of {filename}: {json.dumps(content)}"
    except Exception as e:
        return f"Error: {e}"


class ReadFileTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = read_file
    args_schema: Type[BaseModel] = Type[ReadFileArgs]
    sphere: Autosphere

    def _run(self, *args, **kwargs):
        return super()._run(*args, sphere=self.sphere, **kwargs)


class ReadFile(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = ReadFileTool
    args_schema: Type[BaseModel] = ReadFileArgs
