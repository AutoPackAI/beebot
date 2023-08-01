from random import randint

import pytest

from beebot.body import Body
from beebot.body.body_state_machine import BodyStateMachine


@pytest.fixture()
def body(task):
    body_obj = Body(initial_task=task)
    body_obj.setup()
    body_obj.config.setup_logging()
    body_obj.config.hard_exit = False
    return body_obj


@pytest.fixture()
def task() -> str:
    return "Follow the instructions in the instructions_1.txt file"


@pytest.fixture()
def ids() -> list[str]:
    # ID List length will increase/decrease cost, but increase/decrease the value of the test. 4 is fine.
    length = 4
    range_start = 1
    range_end = 100000
    return [randint(range_start, range_end) for _ in range(length)]


@pytest.fixture()
def instructions_files(body, ids) -> list[str]:
    instructions = []
    for i, instruction in enumerate(ids):
        instructions.append(
            f"The id to remember is {ids[i]}. Read the file instructions_{i + 2}.txt."
        )

    instructions.append("Write the ids previously mentioned to a file named 'ids.txt'.")
    for i, instruction in enumerate(instructions):
        body.file_manager.write_file(f"instructions_{i + 1}.txt", instruction)

    return instructions


def test_parse_history(body, task, instructions_files, ids):
    for i in range(0, 15):
        body.cycle()
        if body.state.current_state == BodyStateMachine.done:
            break

        assert body.state.current_state == BodyStateMachine.waiting

    body.file_manager.flush_to_directory()
    with open("workspace/ids.txt", "r") as f:
        file_contents = f.read()
        for expected_id in ids:
            assert str(expected_id) in file_contents
