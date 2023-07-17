from langchain.prompts import SystemMessagePromptTemplate

TEMPLATE = """As The Tool Selector, you are responsible for choosing the most suitable functions (tools) that an autonomous AI agent can use to accomplish a given task.

Keep in mind functions that may be able to accomplish the task indirectly or in combination with other tools.

Task: {task}

You may only recommend functions from among this list of functions:

{functions_string}

Respond with a comma-separated list of function names, excluding parentheses and arguments. Do not include any other explanatory text.
"""

GET_MORE_TOOLS_TEMPLATE = """**Role: Tool Selector**
As the Tool Selector, your responsibility is to identify the most suitable functions (tools) for an autonomous AI agent to accomplish a given task.

Analyze the functions request below and determine the most suitable functions. Consider functions that can achieve the goal directly or indirectly, in combination with other tools.

**Functions Request**
```
{functions_request}
```

**Task**
To guide your selection, keep in mind the following task:
```
{task}
```

**Functions to Use**
You may only recommend functions from the list below:
```
{functions_string}
```

Please respond with a comma-separated list of function names, excluding parentheses and arguments. Do not include any other explanatory text.

By providing more clarity and emphasizing the consideration of alternative functions, we can ensure better function recommendations that align with the given task.
"""


def initial_selection_template() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(TEMPLATE)


def get_more_tools_template() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(GET_MORE_TOOLS_TEMPLATE)
