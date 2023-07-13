import os

from beebot.body.body import BodyStateMachine
from beebot.config import Config


def test_system_basic_cycle(body):
    assert body.state.current_state == BodyStateMachine.starting

    assert "my_computer.txt" in body.initial_task
    assert isinstance(body.config, Config)
    assert len(body.config.openai_api_key) > 1
    assert len(body.packs) >= 3

    assert body.state.current_state == BodyStateMachine.starting

    for i in range(0, 8):
        body.cycle()
        if body.state.current_state == BodyStateMachine.done:
            break

        assert body.state.current_state == BodyStateMachine.waiting

    assert len(body.packs) >= 5
    with open(os.path.join("workspace", "my_computer.txt"), "r") as f:
        file_contents = f.read()
    assert "Operating System" in file_contents
    assert "Disk Usage" in file_contents
