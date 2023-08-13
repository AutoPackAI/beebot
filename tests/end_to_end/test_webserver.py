import os

import pytest


@pytest.fixture()
def task() -> str:
    return (
        "Create a flask webserver that listens on localhost:9696 and responds to requests to /health with a 200 OK. "
        "Run the webserver in a daemon process. Then Make an HTTP request to the health endpoint and write the "
        "response to health.txt. Once you have written the file, you should kill the webserver process and exit."
    )


@pytest.mark.asyncio
async def test_background_python(body_fixture, task):
    body = await body_fixture

    for i in range(0, 15):
        response = await body.cycle()
        if body.is_done:
            break

        if not response.plan:
            continue

        print(
            f"----\n{await body.current_task_execution.compile_history()}\n{response.plan.plan_text}\n"
            f"{response.decision.tool_name}({response.decision.tool_args})\n{response.observation.response}\n---"
        )

    assert os.path.exists("workspace/health.txt")

    with open("workspace/health.txt", "r") as f:
        file_contents = f.read()
        assert "200" in file_contents
