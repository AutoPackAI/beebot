from beebot.agents.base_agent import BaseAgent
from beebot.packs import (
    ExecutePythonFile,
    ExecutePythonFileInBackground,
    ListProcesses,
    KillProcess,
    InstallPythonPackage,
    Exit,
    ExportVariable,
)
from beebot.packs.filesystem.read_file import ReadFile
from beebot.packs.filesystem.write_file import WriteFile
from beebot.packs.http_request.http_request import HttpRequest
from beebot.packs.write_python_code.write_python_file import WritePythonCode


class CodingAgent(BaseAgent):
    NAME = "Coding Agent"
    DESCRIPTION = "Coding Agent: Excels at writing Python code, executing Python code, and managing processes."
    PACKS = [
        ExecutePythonFile,
        ExecutePythonFileInBackground,
        ListProcesses,
        KillProcess,
        InstallPythonPackage,
        WritePythonCode,
        HttpRequest,
        WriteFile,
        ReadFile,
        Exit,
        ExportVariable,
    ]

    @property
    def planning_prompt_template(self):
        return PLANNING_PROMPT_TEMPLATE

    async def prompt_kwargs(self) -> dict[str, str]:
        kwargs = await super().prompt_kwargs()
        kwargs.pop("file_list")

        structure = []
        documents = await self.task_execution.body.file_manager.all_documents()
        documents.sort(key=lambda d: d.name)
        for document in documents:
            indent_count = len(document.name.split("/"))
            structure.append(f"{' ' * indent_count}- {document.name}")

        if structure:
            kwargs["file_list"] = "\n# Project structure\n" + "\n".join(structure)
        else:
            kwargs["file_list"] = ""
        return {**kwargs}


PLANNING_PROMPT_TEMPLATE = """As the Coding Strategist for an AI Assistant, your role is to strategize and plan coding tasks efficiently and effectively. Avoid redundancy, such as unnecessary immediate verification of actions. You excel at writing Python code and can write entire programs at once without using placeholders.

STDIN / `input()` is not available, take input from argv instead. STDOUT / `print()` is not available, instead save output to files or global variables.

# Functions
## The AI Assistant can call only these functions:
{functions}.

When calling functions provide full data in arguments and avoid using placeholders.

# Task
## Your task is:
{task}

Once the task has been completed, instruct the AI Assistant to call the `exit` function with all arguments to indicate the completion of the task.

{history}
{variables}
{file_list}

# Instructions
Now, devise a concise and adaptable coding plan to guide the AI Assistant. Follow these guidelines:

1. Ensure you interpret the execution history correctly while considering the order of execution. Trust the accuracy of past function executions.
2. Recognize when the task has been successfully completed. If the task has been completed, instruct the AI Assistant to call the `exit` function.
3. Analyze the task carefully to distinguish between actions that the code should take and actions that the AI Assistant should take.
4. Determine the most efficient next action towards completing the task, considering your current information, requirements, and available functions.
5. Direct the execution of the immediate next action using exactly one of the callable functions, making sure to provide all necessary code without placeholders.

Provide a concise analysis of the past history, followed by an overview of your plan going forward, and end with one sentence describing the immediate next action to be taken."""
