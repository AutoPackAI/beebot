import os


def restrict_path(file_path: str, workspace_dir: str):
    absolute_path = os.path.abspath(file_path)
    relative_path = os.path.relpath(absolute_path, workspace_dir)

    if relative_path.startswith("..") or "/../" in relative_path:
        return None

    return absolute_path
