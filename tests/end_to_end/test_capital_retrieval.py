import os

import pytest

from beebot.body.body_state_machine import BodyStateMachine
from beebot.config import Config


@pytest.fixture()
def task():
    return "Create a text file named capital.txt and write the name of the capital of America into it."


@pytest.mark.asyncio
async def test_capital_retrieval(task, body_fixture):
    body = await body_fixture
    assert body.state.current_state == BodyStateMachine.starting

    assert "capital.txt" in body.task
    assert isinstance(body.config, Config)
    assert len(body.config.openai_api_key) > 1
    assert len(body.packs) >= 3

    assert body.state.current_state == BodyStateMachine.starting

    for i in range(0, 8):
        await body.cycle()
        if body.state.current_state == BodyStateMachine.done:
            break

        assert body.state.current_state == BodyStateMachine.waiting

    assert len(body.packs) >= 5
    with open(os.path.join("workspace", "capital.txt"), "r") as f:
        file_contents = f.read()

    assert "washington" in file_contents.lower()
