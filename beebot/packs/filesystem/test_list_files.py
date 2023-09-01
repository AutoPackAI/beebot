import os

from filesystem.list_files import ListFiles


def test_list_files():
    paths = ["a.txt", "b.txt", "c.txt"]
    for path in paths:
        with open(os.path.join("workspace", path), "w+") as f:
            f.write("some string")

    file_list = ListFiles().run(path=".")

    for path in paths:
        assert path in file_list
