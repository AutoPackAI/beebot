# each test runs on cwd to its temp dir
import os
import signal
import sys

import psutil
import pytest
from dotenv import load_dotenv

from beebot.body import Body


@pytest.fixture(autouse=True)
def go_to_tmpdir(request):
    # Get the fixture dynamically by its name.
    tmpdir = request.getfixturevalue("tmpdir")
    # ensure local test created packages can be imported
    sys.path.insert(0, str(tmpdir))

    # In an ideal world we would truly end-to-end pack search, but it's really expensive to do every time, so we copy it
    # source_dir = ".autopack"
    # destination_dir = os.path.join(tmpdir.strpath, ".autopack")
    # shutil.copytree(source_dir, destination_dir)

    print(f"Executing tests in the directory {tmpdir.strpath}")

    # Chdir only for the duration of the test.
    with tmpdir.as_cwd():
        yield


def kill_child_processes(parent_pid: int, sig=signal.SIGKILL):
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for child in children:
        child.send_signal(sig)


@pytest.fixture(autouse=True)
def cleanup_processes():
    yield
    kill_child_processes(os.getpid())


def init_body(task: str):
    body_obj = Body(initial_task=task)
    body_obj.setup()
    body_obj.config.setup_logging()
    body_obj.config.hard_exit = False
    return body_obj


@pytest.fixture(autouse=True)
def load_config():
    load_dotenv()
