import logging
import os
from typing import TYPE_CHECKING

from autopack.filesystem_emulation.file_manager import FileManager
from autopack.pack_config import PackConfig

from beebot.memory import Memory
from beebot.models.database_models import DocumentMemoryModel, DocumentModel

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


class DatabaseFileManager(FileManager):
    """
    This class emulates a filesystem in Postgres, storing files in a simple `document` table with a many-to-many
    relationship with `memory`. Recommended unless you specifically need to access the documents in the filesystem.
    TODO: Include some sort of `flush` system to write the documents to the workspace
    """

    def __init__(
        self, config: PackConfig = PackConfig.global_config(), body: "Body" = None
    ):
        super().__init__(config)
        self.body = body
        self.files = {}

    def active_memory(self) -> Memory:
        return self.body.current_memory_chain.incomplete_memory

    def read_file(self, file_path: str) -> str:
        """Reads a file from the virtual file system in RAM.

        Args:
            file_path (str): The path to the file to be read.

        Returns:
            str: The content of the file. If the file does not exist, returns an error message.
        """
        if document := DocumentModel.select().where(name=file_path).get():
            return document.content
        else:
            return "Error: File not found"

    def write_file(self, file_path: str, content: str) -> str:
        """Writes to a file in the virtual file system in RAM.

        Args:
            file_path (str): The path to the file to be written to.
            content (str): The content to be written to the file.

        Returns:
            str: A success message indicating the file was written.
        """
        document, _created = DocumentModel.get_or_create(
            name=file_path, content=content
        )

        # Get rid of the link between documents with the same filename and the current memory. This looks gross sorry.
        stale_link = (
            DocumentMemoryModel.select()
            .where(
                (DocumentModel.name == file_path)
                & (DocumentMemoryModel.memory == self.active_memory().model_object)
            )
            .join(DocumentModel)
            .first()
        )
        if stale_link:
            logger.warning(f"Deleting stale link ID {stale_link.id}")
            stale_link.delete()

        self.active_memory().add_document(document)
        return f"Successfully wrote {len(content.encode('utf-8'))} bytes to {file_path}"

    async def awrite_file(self, file_path: str, content: str) -> str:
        return self.write_file(file_path, content)

    def delete_file(self, file_path: str) -> str:
        """Deletes a file from the virtual file system in RAM.

        Args:
            file_path (str): The path to the file to be deleted.

        Returns:
            str: A success message indicating the file was deleted. If the file does not exist, returns an error message.
        """
        document = DocumentModel.get(name=file_path).first
        if not document:
            return f"Error: File not found '{file_path}'"

        document_memory = (
            DocumentMemoryModel.select()
            .where(DocumentMemoryModel.document == document)
            .where(DocumentMemoryModel.memory == self.active_memory().model_object)
            .get()
        )
        if document_memory:
            document.delete()
        else:
            # idk why this would happen, perhaps the document hadn't been persisted yet? anyways swallow the error
            logger.warning(
                f"File {file_path} was supposed to be deleted it does not exist"
            )
        return f"Successfully deleted file {file_path}."

    def list_files(self, dir_path: str) -> str:
        """Lists all files in the specified directory in the virtual file system in RAM.

        Args:
            dir_path (str): The path to the directory to list files from.

        Returns:
            str: A list of all files in the directory. If the directory does not exist, returns an error message.
        """
        document_memories = self.active_memory().model_object.document_memories
        file_paths = [dm.document.name for dm in document_memories]

        files_in_dir = [
            file_path
            for file_path in file_paths
            if file_path.startswith(dir_path) and file_path not in self.IGNORE_FILES
        ]
        if files_in_dir:
            return "\n".join(files_in_dir)
        else:
            return f"Error: No such directory {dir_path}."

    def all_documents(self) -> list[DocumentModel]:
        document_memories = (
            DocumentMemoryModel.select()
            .where(DocumentMemoryModel.memory == self.active_memory().model_object)
            .join(DocumentModel)
        )
        return [dm.document for dm in document_memories]

    def load_from_directory(self, directory: str = None):
        if not directory:
            directory = self.body.config.workspace_path

        for file in os.listdir(directory):
            with open(os.path.join(directory, file.replace("/", "_")), "w+") as f:
                self.write_file(file, f.read())

    def flush_to_directory(self, directory: str = None):
        if not directory:
            directory = self.body.config.workspace_path

        for document in self.all_documents():
            with open(
                os.path.join(directory, document.name.replace("/", "_")), "w+"
            ) as f:
                f.write(document.content)

    def document_contents(self) -> str:
        documents = []
        for document in self.all_documents():
            file_details = f"## Contents of file {document.name}"
            documents.append(f"\n{file_details}\n{document.content}")

        if documents:
            return "\n".join(documents)
        return "There are no files available."
