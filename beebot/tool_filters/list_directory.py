import json


def filter_list_directory_output(output: str):
    results = json.dumps(output.split("\n"))
    return f"The files in the directory are: {results}"
