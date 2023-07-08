import os
from typing import Callable, Type

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.autosphere import Autosphere
from beebot.packs.system_pack import SystemBasePack
from beebot.packs.utils import get_module_path

PACK_NAME = "write_file"
PACK_DESCRIPTION = (
    "Allows you to write specified text content to a file, creating a new file or overwriting an existing one as "
    "necessary."
)


class WriteFileArgs(BaseModel):
    filename: str = Field(
        ...,
        description="Specifies the name of the file to which the content will be written.",
    )
    text_content: str = Field(
        ...,
        description="The content that will be written to the specified file.",
    )


def write_file(sphere: Autosphere, filename: str, text_content: str):
    """Write a file to disk. If/when we do sandboxing this provides a convenient way to intervene"""
    try:
        # Just in case they give us a path
        filename = os.path.basename(filename)
        with open(os.path.join(sphere.workspace_path, filename), "w+") as f:
            f.write(text_content)
        return f"Successfully wrote to {filename}"
    except Exception as e:
        return f"Error: {e}"


class WriteFileTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = write_file
    args_schema: Type[BaseModel] = Type[WriteFileArgs]
    sphere: Autosphere

    def _run(self, *args, **kwargs):
        return super()._run(*args, sphere=self.sphere, **kwargs)


class WriteFile(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = WriteFileTool
    args_schema: Type[BaseModel] = WriteFileArgs
