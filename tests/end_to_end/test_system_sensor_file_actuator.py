from beebot.autosphere.autosphere import AutosphereStateMachine
from beebot.config import Config


def test_system_sensor_file_actuator(sphere):
    assert "my_computer.txt" in sphere.initial_task
    assert isinstance(sphere.config, Config)
    assert len(sphere.config.openai_api_key) > 1
    assert len(sphere.packs) >= 3

    assert sphere.state.current_state == AutosphereStateMachine.starting

    for i in range(0, 8):
        assert sphere.state.current_state == AutosphereStateMachine.waiting
        sphere.cycle()
        if sphere.state.current_state == AutosphereStateMachine.done:
            break

        assert sphere.state.current_state == AutosphereStateMachine.waiting

    assert len(sphere.packs) >= 8
    with open("my_computer.txt", "r") as f:
        file_contents = f.read()
    assert "Operating System" in file_contents
    assert "Disk Usage" in file_contents
