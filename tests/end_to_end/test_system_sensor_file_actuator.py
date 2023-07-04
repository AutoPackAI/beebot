from beebot.autosphere import Autosphere
from beebot.config import Config


def test_system_sensor_file_actuator():
    task = "Get my OS name and version, and my current disk usage. write it to a file called my_computer.txt"
    sphere = Autosphere.init(task)

    assert sphere.initial_task == task
    assert "my_computer.txt" in sphere.task
    assert isinstance(sphere.config, Config)
    assert len(sphere.config.openai_api_key) > 1
    import pdb
    pdb.set_trace()
    return
