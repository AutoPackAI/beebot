import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from beebot.body import Body


def list_files(body: "Body") -> list[str]:
    """List a file from disk. If/when we do sandboxing this provides a convenient way to intervene"""
    directory = body.config.workspace_path
    file_basenames = [
        os.path.basename(file)
        for file in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, file))
    ]
    return file_basenames


def restrict_path(file_path: str, workspace_dir: str):
    absolute_path = os.path.abspath(file_path)
    relative_path = os.path.relpath(absolute_path, workspace_dir)

    if relative_path.startswith("..") or "/../" in relative_path:
        return None

    return absolute_path


def files_documents(files: list[str]) -> str:
    documents = []
    for file in files:
        file_details = f"## Contents of file {file}"
        with open(os.path.join("workspace", file), "r+") as f:
            file_contents = f.read()

        documents.append(f"\n{file_details}\n{file_contents}")

    if documents:
        return "\n".join(documents)
    return "There are no files available."
