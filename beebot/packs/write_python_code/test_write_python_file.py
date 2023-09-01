import os

from write_python_code.write_python_file import WritePythonCode


def test_write_python_file_success():
    pack = WritePythonCode(workspace_path="workspace")
    code = "print('Hello world!')"
    file_name = "hello_world.py"
    result = pack.run(file_name=file_name, code=code)

    assert result == f"Compiled successfully and saved to hello_world.py."

    with open(os.path.join("workspace", file_name), "r") as f:
        assert f.read() == code


def test_write_python_file_compile_error():
    pack = WritePythonCode(workspace_path="workspace")
    code = "asdf!"
    file_name = "error.py"
    result = pack.run(file_name=file_name, code=code)

    assert "invalid syntax" in result

    assert not os.path.exists(os.path.join("workspace", file_name))
