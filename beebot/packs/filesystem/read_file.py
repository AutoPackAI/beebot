from autopack import Pack
from pydantic import BaseModel, Field


class ReadFileArgs(BaseModel):
    filename: str = Field(
        ...,
        description="The name of the file to be read.",
    )


class ReadFile(Pack):
    name = "read_file"
    description = "Reads and returns the content of a specified file from the disk."
    args_schema = ReadFileArgs
    categories = ["Files"]

    def _run(self, filename: str) -> str:
        return self.filesystem_manager.read_file(filename)

    async def _arun(self, filename: str) -> str:
        return await self.filesystem_manager.aread_file(filename)
