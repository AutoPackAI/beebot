# each test runs on cwd to its temp dir
import sys
from unittest.mock import patch

import pytest
from dotenv import load_dotenv

from beebot.autosphere import Autosphere


@pytest.fixture(autouse=True)
def go_to_tmpdir(request):
    # Get the fixture dynamically by its name.
    tmpdir = request.getfixturevalue("tmpdir")
    # ensure local test created packages can be imported
    sys.path.insert(0, str(tmpdir))

    # Chdir only for the duration of the test.
    with tmpdir.as_cwd():
        yield


@pytest.fixture()
def simple_task():
    return "Get my OS name and version, and my current disk usage. write it to a file called my_computer.txt"


@pytest.fixture()
def sphere(simple_task):
    return Autosphere(initial_task=simple_task)


@pytest.fixture(autouse=True)
def mock_run_exit(sphere):
    def mocked_run_exit():
        sphere.state.finish()

    with patch("beebot.packs.exit.run_exit", side_effect=mocked_run_exit):
        yield


@pytest.fixture(autouse=True)
def load_config():
    load_dotenv()
