FORMAT_SECTION = """
Please respond in the following format:

Firstly, provide a comma-separated list of function names. Exclude parentheses and arguments from this list. Secondly, after the special delimiter '###', provide explanations for why each function was chosen and how it contributes to accomplishing the task.

For example, your response may look like this:

function1, function2, function3 ### function1 can accomplish step A of the task because..., function2 and function3 can be used together to..."""

INITIAL_SELECTION_TEMPLATE = """As the AI Tool Selector, your responsibility is to analyze a given task and the available functions. Your goal is to identify and recommend functions (tools) that could be used, either directly or indirectly, to accomplish the task by an autonomous AI agent.

By providing more flexibility in the selection and emphasizing the consideration of alternative functions, we can ensure a wider range of function recommendations that align with the given task.

Take into account that programming functions should only be recommended if the task explicitly requires programming.

# Task
Your original task, given by the human, is:
{task}

# Functions
You may only recommend functions from the following list:
{functions}.

When making your recommendations, consider how the functions can work together to achieve the task's goal, how certain functions may be more effective than others, and prioritize those functions that are most likely to contribute to a successful task completion."""

GET_MORE_TOOLS_TEMPLATE = """As the AI Tool Selector, your responsibility is to identify functions (tools) that could be useful for an autonomous AI agent to accomplish a given task. By providing more flexibility in the selection and emphasizing the consideration of alternative functions, we can ensure a wider range of function recommendations that align with the given task.

Only recommend programming functions if the task explicitly requires programming.

In this scenario, the Autonomous AI has made a request for additional tools to complete a task. Your role is to analyze the functions request and determine which functions could be useful, either directly or indirectly, in combination with other tools.

Request for more tools:
The Autonomous AI has made this request for more tools: {functions_request}

Original Task:
The task originally assigned by the human is:
{task}

Available functions:
You may only recommend functions from the following list:
{functions}."""


def initial_selection_template() -> str:
    return INITIAL_SELECTION_TEMPLATE + FORMAT_SECTION


def get_more_tools_template() -> str:
    return GET_MORE_TOOLS_TEMPLATE + FORMAT_SECTION
