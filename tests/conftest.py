# each test runs on cwd to its temp dir
import asyncio
import os
import signal
import sys

import psutil
import pytest
from _pytest.fixtures import FixtureRequest
from dotenv import load_dotenv
from tortoise import Tortoise

from beebot.body import Body
from beebot.models.database_models import initialize_db


def pytest_configure():
    load_dotenv()


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


def db_url() -> str:
    return os.environ.get("TORTOISE_TEST_DB", "sqlite://:memory:")


@pytest.fixture(autouse=True)
async def initialize_tests(request: FixtureRequest):
    await initialize_db(db_url())

    def fin():
        async def afin():
            if "postgres" not in db_url():
                await Tortoise._drop_databases()

        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(afin())

    request.addfinalizer(fin)


@pytest.fixture()
async def body_fixture(task: str, initialize_tests, go_to_tmpdir):
    await initialize_tests
    body_obj = Body(task=task)
    await body_obj.setup()
    body_obj.config.setup_logging()
    body_obj.config.hard_exit = False
    return body_obj
