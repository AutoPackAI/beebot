from langchain.prompts import SystemMessagePromptTemplate

TEMPLATE = """Given the task and the function list provided below, identify the functions that would be most suitable for completing every element of the task.

Task: {task}

You may only recommend functions from among this list of functions:

{functions_string}

Respond with a comma-separated list of function names, excluding parentheses and arguments. Do not include any other explanatory text.
"""

GET_MORE_TOOLS_TEMPLATE = """Given a functions request, the task, the plan and the function list provided below, identify the functions that would be most suitable for completing every element of the task.

Functions Request:
{functions_request}

Task: {task}

Plan:
{plan}

You may only recommend functions from among this list of functions:

{functions_string}

Respond with a comma-separated list of function names, excluding parentheses and arguments. Do not include any other explanatory text.
"""


def initial_selection_template() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(TEMPLATE)


def get_more_tools_template() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(GET_MORE_TOOLS_TEMPLATE)
