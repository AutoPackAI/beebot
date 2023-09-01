import json
from typing import TYPE_CHECKING

from beebot.body.pack_utils import functions_detail_list
from beebot.planner.planning_prompt import planning_prompt_template

if TYPE_CHECKING:
    from beebot.execution.task_execution import TaskExecution


class BaseAgent:
    NAME = ""
    PACKS = []
    DESCRIPTION = ""

    def __init__(self, task_execution: "TaskExecution"):
        self.task_execution = task_execution

    @property
    def planning_prompt_template(self) -> str:
        return planning_prompt_template()

    @property
    def variables(self) -> dict[str, list[str]]:
        return self.task_execution.variables

    async def prompt_kwargs(self) -> dict[str, str]:
        task = self.task_execution.instructions
        variables = self.compile_variables()

        files = []
        for document in await self.task_execution.body.file_manager.all_documents():
            files.append(document.name)

        functions = functions_detail_list(self.task_execution.packs.values())
        history = await self.task_execution.compile_history()

        if files:
            file_list = ", ".join(files)
            file_section = f"\n# Files\n## The AI Assistant has access to the following files: {file_list}"
        else:
            file_section = ""

        if history:
            history_section = (
                "# History:\n## The AI Assistant has a history of functions that the AI Assistant has already executed for this "
                f"task. Here is the history, in order, starting with the first function executed:\n{history}"
            )
        else:
            history_section = ""

        return {
            "task": task,
            "functions": functions,
            "file_list": file_section,
            "variables": variables,
            "history": history_section,
        }

    async def planning_prompt(self) -> tuple[str, dict[str, str]]:
        prompt_variables = await self.prompt_kwargs()
        return (
            self.planning_prompt_template.format(**prompt_variables),
            prompt_variables,
        )

    def compile_variables(self) -> str:
        variable_table = []

        for value, names in self.variables.items():
            if value:
                name_equals = " = ".join(names)
                variable_row = f'{name_equals} = """{value}"""'
                variable_table.append(variable_row)

        for name, value in self.task_execution.body.global_variables.items():
            if value:
                variable_row = f'global {name} = """{value}"""'
                variable_table.append(variable_row)

        if not variable_table:
            return ""

        header = (
            "\n# Variables\n## The AI Assistant has access to these variables. Variables are local unless explicitly "
            'declared as global. Each variable is a string with the value enclosed in triple quotes ("""):\n'
        )
        return header + "\n".join(variable_table)

    async def compile_history(self) -> str:
        if not self.task_execution.steps:
            return ""

        step_table = []
        used_variables = []

        for step in self.task_execution.steps:
            if not step.observation:
                continue

            outcome = step.observation.response

            variable_names = self.variables.get(outcome)
            try:
                variable_name = next(
                    name for name in variable_names if name not in used_variables
                )
            except StopIteration:
                variable_name = variable_names[-1]

            used_variables.append(variable_name)

            tool_arg_list = [
                f"{name}={json.dumps(value)}"
                for name, value in step.decision.tool_args.items()
            ]
            tool_args = ", ".join(tool_arg_list)

            if outcome and outcome in self.variables:
                step_table.append(
                    f">>> {variable_name} = {step.decision.tool_name}({tool_args})"
                )
            else:
                step_table.append(f">>> {step.decision.tool_name}({tool_args})")

            if not step.observation.success or outcome.startswith("Error"):
                step_table.append(step.observation.error_reason or outcome)
            else:
                step_table.append(
                    f"Success! Result stored in local variable {variable_name}."
                )

        return "\n".join(step_table)
