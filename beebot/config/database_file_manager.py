import logging
import os
from typing import TYPE_CHECKING, Union

from autopack.filesystem_emulation.file_manager import FileManager
from autopack.pack_config import PackConfig

from beebot.execution import Step
from beebot.models.database_models import DocumentModel, DocumentStep

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)

IGNORE_FILES = ["poetry.lock", "pyproject.toml", "__pycache__"]


class DatabaseFileManager(FileManager):
    """
    This class emulates a filesystem in Postgres, storing files in a simple `document` table with a many-to-many
    relationship with `execution`. Recommended unless you specifically need to access the documents in the filesystem.
    """

    def __init__(
        self, config: PackConfig = PackConfig.global_config(), body: "Body" = None
    ):
        super().__init__(config)
        self.body = body
        self.files = {}

    @property
    def current_step(self) -> Union[Step, None]:
        task = self.body.current_task_execution or self.body.task_executions[-1]
        if not task:
            return None
        try:
            return task.steps[-1]
        except IndexError:
            return None

    # Can't support sync db access without a lot of headaches
    def read_file(self, *args, **kwargs):
        raise NotImplementedError

    def write_file(self, *args, **kwargs):
        raise NotImplementedError

    def delete_file(self, *args, **kwargs):
        raise NotImplementedError

    def list_files(self, *args, **kwargs):
        raise NotImplementedError

    async def aread_file(self, file_path: str) -> str:
        """Reads a file from the virtual file system in RAM.

        Args:
            file_path (str): The path to the file to be read.

        Returns:
            str: The content of the file. If the file does not exist, returns an error message.
        """
        documents = await self.current_step.documents
        document = documents.get(file_path)
        if document:
            return document.content
        else:
            nonlocal_file = await DocumentModel.get_or_none(name=file_path)
            if nonlocal_file:
                return nonlocal_file.content
            return "Error: File not found"

    async def awrite_file(self, file_path: str, content: str) -> str:
        """Writes to a file in the virtual file system in RAM.

        Args:
            file_path (str): The path to the file to be written to.
            content (str): The content to be written to the file.

        Returns:
            str: A success message indicating the file was written.
        """
        if not self.current_step:
            return ""

        document, _created = await DocumentModel.get_or_create(
            name=file_path, content=content
        )

        stale_link = await DocumentStep.filter(
            document__name=file_path, step=self.current_step.model_object
        ).first()

        if stale_link:
            logger.warning(f"Deleting stale link ID {stale_link.id}")
            await stale_link.delete()

        await self.current_step.add_document(document)
        return f"Successfully wrote {len(content.encode('utf-8'))} bytes to {file_path}"

    async def adelete_file(self, file_path: str) -> str:
        """Deletes a file from the virtual file system in RAM.

        Args:
            file_path (str): The path to the file to be deleted.

        Returns:
            str: A success message indicating the file was deleted. If the file does not exist, returns an error message.
        """
        if not self.current_step:
            return ""

        document = await DocumentModel.get_or_none(name=file_path)
        if not document:
            return f"Error: File not found '{file_path}'"

        document_step = await DocumentStep.filter(
            document=document, step=self.current_step.model_object
        ).first()

        if document_step:
            await document.delete()
        else:
            logger.warning(
                f"File {file_path} was supposed to be deleted but it does not exist"
            )

        return f"Successfully deleted file {file_path}."

    async def alist_files(self, dir_path: str) -> str:
        """Lists all files in the specified directory in the virtual file system in RAM.

        Args:
            dir_path (str): The path to the directory to list files from.

        Returns:
            str: A list of all files in the directory. If the directory does not exist, returns an error message.
        """
        if not self.current_step:
            return ""

        document_steps = await DocumentStep.filter(
            step=self.current_step.model_object
        ).prefetch_related("document")

        file_paths = [dm.document.name for dm in document_steps]

        files_in_dir = [
            file_path
            for file_path in file_paths
            if file_path.startswith(dir_path) and file_path not in self.IGNORE_FILES
        ]
        if files_in_dir:
            return "\n".join(files_in_dir)
        else:
            return f"Error: No such directory {dir_path}."

    async def all_documents(self) -> list[DocumentModel]:
        if not self.current_step:
            return []
        document_steps = await DocumentStep.filter(
            step=self.current_step.model_object
        ).prefetch_related("document")

        return [dm.document for dm in document_steps]

    async def load_from_directory(self, directory: str = None):
        if not directory:
            directory = self.body.config.workspace_path

        for file in os.listdir(directory):
            abs_path = os.path.abspath(os.path.join(directory, file.replace("/", "_")))
            if not os.path.isdir(abs_path) and file not in IGNORE_FILES:
                with open(abs_path, "r") as f:
                    await self.awrite_file(file, f.read())

    async def flush_to_directory(self, directory: str = None):
        if not self.current_step:
            return

        if not directory:
            directory = self.body.config.workspace_path

        all_documents = await self.all_documents()
        for document in all_documents:
            with open(
                os.path.join(directory, document.name.replace("/", "_")), "w+"
            ) as f:
                f.write(document.content)
