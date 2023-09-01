import os

import pytest

from beebot.config import Config


@pytest.fixture()
def task():
    return "Write to a file called output.txt containing tesla's revenue in 2022."


@pytest.mark.asyncio
async def test_revenue_lookup(task, body_fixture):
    body = await body_fixture

    assert "tesla" in body.task.lower()
    assert "2022" in body.task
    assert isinstance(body.config, Config)
    assert len(body.config.openai_api_key) > 1
    assert len(body.current_task_execution.packs) >= 3

    for i in range(0, 8):
        await body.cycle()
        if body.is_done:
            break

    with open(os.path.join("workspace", "output.txt"), "r") as f:
        file_contents = f.read()

    assert "81" in file_contents
