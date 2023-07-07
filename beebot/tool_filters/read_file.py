def filter_read_file_output(output: str):
    if "Error" in output:
        return output

    return f"The contents of the file are: {output}"
