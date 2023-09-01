import os

from filesystem.read_file import ReadFile


def test_read_file():
    with open(os.path.join("workspace", "some_file.txt"), "w+") as f:
        f.write("some string")

    assert ReadFile().run(filename="some_file.txt") == "some string"
