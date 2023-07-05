import os

from beebot.autosphere import Autosphere
from beebot.autosphere.autosphere import AutosphereStateMachine
from beebot.config import Config


def test_system_sensor_file_actuator():
    task = "Get my OS name and version, and my current disk usage. write it to a file called my_computer.txt"
    sphere = Autosphere.init(task)

    assert sphere.initial_task == task
    assert "my_computer.txt" in sphere.task
    assert isinstance(sphere.config, Config)
    assert len(sphere.config.openai_api_key) > 1
    assert len(sphere.packs) >= 3

    assert sphere.state.current_state == AutosphereStateMachine.starting

    output = ""
    for i in range(0, 3):
        output = sphere.cycle()
        assert output.success

        if os.path.exists("my_computer.txt"):
            break

        assert sphere.state.current_state == AutosphereStateMachine.waiting
        assert type(output.response) == dict
        assert (
            "os_name" in output.response.keys()
            or "total_bytes" in output.response.keys()
        )

    assert sphere.state.current_state == AutosphereStateMachine.waiting
    assert type(output.response) == dict
    assert "my_computer.txt" in output.response.get("output")

    with open("my_computer.txt", "r") as f:
        file_contents = f.read()
    assert "Operating System" in file_contents
    assert "Disk Usage" in file_contents

    sphere.cycle()
    assert sphere.state.current_state == AutosphereStateMachine.done
