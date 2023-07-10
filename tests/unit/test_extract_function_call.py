from beebot.brainstem.brainstem import extract_function_call_from_response


def test_extract_function_call_from_response():
    response = """This will create a file named "my_computer.txt" and write the operating system name, version, and disk usage information to it.
After executing this function, I will call the `exit` function to signal that the task is complete.
```typescript
functions.exit({
  success: true,
  conclusion: "The operating system name, version, and disk usage information has been saved to the file 'my_computer.txt'.",
  process_summary: "The task was completed successfully.",
  function_summary: "The required functions were used efficiently."
});
```"""
    method, args = extract_function_call_from_response(response)

    assert method == "exit"
    assert args == {
        "success": True,
        "conclusion": "The operating system name, version, and disk usage information has been saved to the file "
        "'my_computer.txt'.",
        "process_summary": "The task was completed successfully.",
        "function_summary": "The required functions were used efficiently.",
    }
