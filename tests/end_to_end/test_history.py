import os
from random import randint

import pytest

from beebot.body.body import BodyStateMachine
from tests.conftest import init_body


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
def instructions_files(ids) -> list[str]:
    os.makedirs("workspace", exist_ok=True)
    instructions = []
    for i, instruction in enumerate(ids):
        with open(f"workspace/instructions_{i + 1}.txt", "w+") as f:
            if i >= len(ids):
                instruction = (
                    f"The id to remember is {ids[i]}. Read the file instructions_{i + 1}.txt.",
                )
            else:
                instruction = (
                    "Write the ids previously mentioned to a file named 'ids.txt'."
                )

            instructions.append(instruction)
            f.write(instruction)

    return instructions


def test_parse_history(task, instructions_files, ids):
    body = init_body(task)

    for i in range(0, 15):
        body.cycle()
        if body.state.current_state == BodyStateMachine.done:
            break

        assert body.state.current_state == BodyStateMachine.waiting

    with open("workspace/ids.txt", "r") as f:
        file_contents = f.read()
        for expected_id in ids:
            assert str(expected_id) in file_contents
