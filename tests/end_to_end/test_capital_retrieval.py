import os

import pytest

from beebot.config import Config


@pytest.fixture()
def task():
    return "Create a text file named capital.txt and write the name of the capital of America into it."


@pytest.mark.asyncio
async def test_capital_retrieval(task, body_fixture):
    body = await body_fixture

    assert "capital.txt" in body.task
    assert isinstance(body.config, Config)
    assert len(body.config.openai_api_key) > 1
    assert len(body.current_task_execution.packs) >= 3

    for i in range(0, 8):
        await body.cycle()
        if body.is_done:
            break

    with open(os.path.join("workspace", "capital.txt"), "r") as f:
        file_contents = f.read()

    assert "washington" in file_contents.lower()
