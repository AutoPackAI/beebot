from autopack import Pack
from pydantic import BaseModel, Field

# A few Packs will use poetry inside of the workspace, and the AI gets hella confused when these files are present.
IGNORE_FILES = ["pyproject.toml", "poetry.lock"]


class ListFilesArgs(BaseModel):
    path: str = Field(description="The directory to list the files of")


class ListFiles(Pack):
    name = "list_files"
    description = "Provides a list of all accessible files in a given path."
    args_schema = ListFilesArgs
    categories = ["Files"]

    def _run(self, path: str):
        return self.filesystem_manager.list_files(path)

    async def _arun(self, path: str) -> str:
        return await self.filesystem_manager.alist_files(path)
