import json


def filter_read_file_output(output: str):
    return json.dumps(output)
    if "Error" in output:
        return output

    return f"The contents of the file are: {json.dumps(output)}"
