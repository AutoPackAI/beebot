from typing import Type

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "delete_file"
PACK_DESCRIPTION = "Deletes a file from disk."


class DeleteFileArgs(BaseModel):
    filename: str = Field(..., description="The basename of the file to be deleted")


class DeleteFile(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = DeleteFileArgs
    categories: list[str] = ["Files"]

    def _run(self, filename: str) -> str:
        """The AI sucks at choosing when to delete files and because it's dangerous we almost never want to do it. So
        let's just not do it."""
        return f"{filename} deleted."
