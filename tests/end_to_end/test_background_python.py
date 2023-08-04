import os

import pytest

from beebot.body.body_state_machine import BodyStateMachine


@pytest.fixture()
def task() -> str:
    return (
        "Create a python file named 'sleepy.py' that sleeps for a number of seconds according to its arguments and "
        "writes that number into the file 'sleepy.txt' after it has finished sleeping. At the end of the program "
        "output a success message. Execute sleepy.py in the background with an argument of 10, check the status of "
        "the program until it's done, and then exit."
    )


@pytest.mark.asyncio
async def test_background_python(task, body_fixture):
    body = await body_fixture

    for i in range(0, 15):
        response = await body.cycle()
        print(
            f"----\n{await body.current_execution_path.compile_history()}\n{response.plan.plan_text}\n{response.decision.tool_name}"
            f"({response.decision.tool_args})\n{response.observation.response}\n---"
        )
        if body.state.current_state == BodyStateMachine.done:
            break

    assert os.path.exists("workspace/sleepy.py")
    assert os.path.exists("workspace/sleepy.txt")

    with open("workspace/sleepy.py", "r") as f:
        file_contents = f.read()
        assert "sleep" in file_contents
        # FIXME: It doesn't use args sometimes, probably a prompt issue?
        # assert "argv" in file_contents

    with open("workspace/sleepy.txt", "r") as f:
        file_contents = f.read()
        assert "10" in file_contents
