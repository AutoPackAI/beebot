FORMAT_SECTION = """

Please respond in the following format:

Firstly, provide a comma-separated list of function names. Exclude parentheses and arguments from this list. Secondly, after listing all functions, put the special delimiter '###', then provide explanations for why each function was chosen and how it contributes to accomplishing the task.

For example, your response may look like this:

function1, function2, function3
###
function1 can accomplish step A of the task because..., function2 and function3 can be used together to..."""

INITIAL_SELECTION_TEMPLATE = """As the AI Tool Selector your responsibility is to identify functions (tools) that could be useful for an autonomous AI assistant to accomplish a given task. Functions are general-purpose and intended to be used in a wide variety of tasks.

By providing more flexibility in the selection and emphasizing the consideration of alternative functions, we can ensure a wider range of function recommendations that align with the given task.

Only recommend programming functions if the task explicitly requires writing code.

Analyze the task and available functions, and determine which functions could be useful. Consider functions that can achieve the goal directly or indirectly, in combination with other tools.

# Task
Your original task, given by the human, is:
{task}

Existing functions:
The AI Assistant already has access to these existing functions:
{existing_functions}

# Functions
You may only recommend functions from the following list:
{functions}.

When making your recommendations, consider how the functions can work together to achieve the task's goal, how certain functions may be more effective than others, and prioritize those functions that are most likely to contribute to a successful task completion."""

GET_MORE_TOOLS_TEMPLATE = """As the AI Tool Selector, your responsibility is to identify functions that could be useful for an autonomous AI assistant to accomplish a given task. Functions are general-purpose and intended to be used in a wide variety of tasks.

By providing more flexibility in the selection and emphasizing the consideration of alternative functions, we can ensure a wider range of function recommendations that align with the given task.

Only recommend programming functions if the task explicitly requires writing code.

In this scenario, the Autonomous AI has made a request for additional functions to complete a task. Your role is to analyze the functions request and determine which functions could be useful, either directly or indirectly, in combination with other functions.

The Autonomous AI has made this request for more functions: {functions_request}

Original Task:
The task originally assigned by the human is:
{task}

Existing functions:
The AI Assistant already has access to these existing functions:
{existing_functions}

Available functions:
You may only recommend functions from the following list:
{functions}."""


def initial_selection_template() -> str:
    return INITIAL_SELECTION_TEMPLATE + FORMAT_SECTION


def acquire_new_functions_template() -> str:
    return GET_MORE_TOOLS_TEMPLATE + FORMAT_SECTION
