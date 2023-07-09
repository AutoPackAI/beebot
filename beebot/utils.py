import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from beebot.autosphere import Autosphere


def list_files(sphere: "Autosphere"):
    """List a file from disk. If/when we do sandboxing this provides a convenient way to intervene"""
    directory = sphere.config.workspace_path
    file_basenames = [
        os.path.basename(file)
        for file in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, file))
    ]
    return json.dumps(file_basenames)
