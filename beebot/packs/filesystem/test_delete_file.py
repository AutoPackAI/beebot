import os

from filesystem.delete_file import DeleteFile


def test_read_file():
    path = "some_file_to_delete.txt"
    with open(os.path.join("workspace", path), "w+") as f:
        f.write("some string")

    DeleteFile().run(filename=path)

    assert not os.path.exists(path)
