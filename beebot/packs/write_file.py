import logging
import os
from typing import Callable, Type

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.body import Body
from beebot.body.pack_utils import get_module_path
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "write_file"
PACK_DESCRIPTION = (
    "Allows you to write specified text content to a file, creating a new file or overwriting an existing one as "
    "necessary."
)

logger = logging.getLogger(__name__)


class WriteFileArgs(BaseModel):
    filename: str = Field(
        ...,
        description="Specifies the name of the file to which the content will be written.",
    )
    text_content: str = Field(
        ...,
        description="The content that will be written to the specified file.",
    )


def write_file(body: Body, filename: str, text_content: str):
    """Write a file to disk. If/when we do sandboxing this provides a convenient way to intervene"""
    try:
        # Just in case they give us a path
        filename = os.path.basename(filename)
        file_path = os.path.join(body.config.workspace_path, filename)
        with open(file_path, "w+") as f:
            f.write(text_content)
        logger.info(f"Successfully wrote to {file_path}")
        return f"Successfully wrote to {filename}"
    except Exception as e:
        return f"Error: {e}"


class WriteFileTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = write_file
    args_schema: Type[BaseModel] = Type[WriteFileArgs]
    body: Body

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class WriteFile(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = WriteFileTool
    args_schema: Type[BaseModel] = WriteFileArgs
