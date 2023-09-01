from autopack import Pack
from pydantic import BaseModel, Field


class DeleteFileArgs(BaseModel):
    filename: str = Field(..., description="The basename of the file to be deleted")


class DeleteFile(Pack):
    name = "delete_file"
    description = "Deletes a file from disk."
    args_schema = DeleteFileArgs
    categories = ["Files"]

    def _run(self, filename: str) -> str:
        return self.filesystem_manager.delete_file(filename)

    async def _arun(self, filename: str) -> str:
        return self.filesystem_manager.adelete_file(filename)
