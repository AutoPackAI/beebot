import os
from typing import Type

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "read_file"
PACK_DESCRIPTION = "Reads and returns the content of a specified file from the disk."


class ReadFileArgs(BaseModel):
    filename: str = Field(
        ...,
        description="The name of the file to be read.",
    )


class ReadFile(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = ReadFileArgs

    def _run(self, filename: str) -> str:
        """Read a file from disk. If/when we do sandboxing this provides a convenient way to intervene"""
        try:
            # Just in case they give us a path
            filename = os.path.basename(filename)
            file_path = os.path.join(self.body.config.workspace_path, filename)
            if not os.path.exists(file_path):
                return "Error: No such file"

            with open(file_path, "r") as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error: {e}"
