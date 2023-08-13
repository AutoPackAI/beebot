import logging

from autopack import Pack
from pydantic import BaseModel, Field

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


class WriteFile(Pack):
    name = "write_file"
    description = PACK_DESCRIPTION
    args_schema = WriteFileArgs
    categories = ["Files"]

    # TODO: This can be reversible for some, but not all, file manager types
    reversible = False

    def _run(self, filename: str, text_content: str):
        return self.filesystem_manager.write_file(filename, text_content)

    async def _arun(self, filename: str, text_content: str) -> str:
        return await self.config.filesystem_manager.awrite_file(filename, text_content)
