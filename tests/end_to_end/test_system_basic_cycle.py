import os

import pytest

from beebot.config import Config


@pytest.fixture()
def task():
    return "Get my OS name and version, and my current disk usage. write it to a file called my_computer.txt"


@pytest.mark.asyncio
async def test_system_basic_cycle(task, body_fixture):
    body = await body_fixture

    assert "my_computer.txt" in body.task
    assert isinstance(body.config, Config)
    assert len(body.config.openai_api_key) > 1

    for i in range(0, 8):
        await body.cycle()
        if body.is_done:
            break

    with open(os.path.join("workspace", "my_computer.txt"), "r") as f:
        file_contents = f.read()
    assert "Operating System" in file_contents or "OS" in file_contents
    assert "GB" in file_contents
