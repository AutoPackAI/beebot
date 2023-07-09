# each test runs on cwd to its temp dir
import os
import shutil
import sys

import pytest
from dotenv import load_dotenv

from beebot.autosphere import Autosphere


@pytest.fixture(autouse=True)
def go_to_tmpdir(request):
    # Get the fixture dynamically by its name.
    tmpdir = request.getfixturevalue("tmpdir")
    # ensure local test created packages can be imported
    sys.path.insert(0, str(tmpdir))

    # In an ideal world we would truly end-to-end pack search, but it's really expensive to do every time, so we copy it
    source_dir = ".autopack"
    destination_dir = os.path.join(tmpdir.strpath, ".autopack")
    shutil.copytree(source_dir, destination_dir)

    # Chdir only for the duration of the test.
    with tmpdir.as_cwd():
        yield


@pytest.fixture()
def simple_task():
    return "Get my OS name and version, and my current disk usage. write it to a file called my_computer.txt"


@pytest.fixture()
def sphere(simple_task):
    sphere_obj = Autosphere(initial_task=simple_task)
    sphere_obj.setup()
    sphere_obj.config.hard_exit = False
    return sphere_obj


@pytest.fixture(autouse=True)
def load_config():
    load_dotenv()
