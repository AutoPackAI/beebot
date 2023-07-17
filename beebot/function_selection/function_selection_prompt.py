from langchain.prompts import SystemMessagePromptTemplate

TEMPLATE = """As the AI Tool Selector your responsibility is to identify functions (tools) that could be useful for an autonomous AI agent to accomplish a given task.

Analyze the task and available functions, and determine which functions could be useful. Consider functions that can achieve the goal directly or indirectly, in combination with other tools.

When a task involves coding, prioritize tools that can execute code. Also, keep an eye on functions that, even if not explicitly coding-related, may indirectly aid in achieving the task objectives when combined with other tools.

Only recommend programming functions if the task explicitly requires programming.

Task:
Your original task, given by the human, is:
{task}

Available functions:
You may only recommend functions from the following list:
{functions}.

Please respond with a comma-separated list of function names, excluding parentheses and arguments. Do not include any other explanatory text.

By providing more flexibility in the selection and emphasizing the consideration of alternative functions, we can ensure a wider range of function recommendations that align with the given task.
"""

GET_MORE_TOOLS_TEMPLATE = """As the AI Tool Selector your responsibility is to identify functions (tools) that could be useful for an autonomous AI agent to accomplish a given task.

Analyze the functions request and determine which functions could be useful. Consider functions that can achieve the goal directly or indirectly, in combination with other tools.

Only recommend programming functions if the task explicitly requires programming.

Functions request:
The Autonomous AI has made this request for more tools: {functions_request}

Task:
Your original task, given by the human, is:
{task}

Available functions:
You may only recommend functions from the following list:
{functions}.

Please respond with a comma-separated list of function names, excluding parentheses and arguments. Do not include any other explanatory text.

By providing more flexibility in the selection and emphasizing the consideration of alternative functions, we can ensure a wider range of function recommendations that align with the given task.
"""


def initial_selection_template() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(TEMPLATE)


def get_more_tools_template() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(GET_MORE_TOOLS_TEMPLATE)
