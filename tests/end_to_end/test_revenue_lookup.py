import os

import pytest

from beebot.body.body_state_machine import BodyStateMachine
from beebot.config import Config


@pytest.fixture()
def task():
    return "Write to a file called output.txt containing tesla's revenue in 2022."


@pytest.mark.asyncio
async def test_revenue_lookup(task, body_fixture):
    body = await body_fixture
    assert body.state.current_state == BodyStateMachine.oversight

    assert "Tesla" in body.task
    assert "2022" in body.task
    assert isinstance(body.config, Config)
    assert len(body.config.openai_api_key) > 1
    assert len(body.packs) >= 3

    for i in range(0, 8):
        await body.cycle()
        if body.state.current_state == BodyStateMachine.done:
            break

    assert len(body.packs) >= 5
    with open(os.path.join("workspace", "output.txt"), "r") as f:
        file_contents = f.read()

    assert "81" in file_contents
