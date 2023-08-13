import os

from filesystem.write_file import WriteFile


def test_write_file():
    WriteFile().run(filename="some_file_to_write.txt", text_content="some string")

    with open(os.path.join("workspace", "some_file_to_write.txt"), "r") as f:
        assert f.read() == "some string"
