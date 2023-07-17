import logging
import os
from typing import Type

from pydantic import BaseModel, Field

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


class WriteFile(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = WriteFileArgs
    categories: list[str] = ["Files"]
    # TODO: Make this reversible I guess by storing files in memory?
    reversible = False

    def _run(self, filename: str, text_content: str):
        """Write a file to disk. If/when we do sandboxing this provides a convenient way to intervene"""
        try:
            # Just in case they give us a path
            filename = os.path.basename(filename)
            file_path = os.path.join(self.body.config.workspace_path, filename)
            with open(file_path, "w+") as f:
                f.write(text_content)
            logger.info(f"Successfully wrote to {file_path}")
            return f"Successfully wrote {len(text_content.encode('utf-8'))} bytes to {filename}"
        except Exception as e:
            return f"Error: {e}"
