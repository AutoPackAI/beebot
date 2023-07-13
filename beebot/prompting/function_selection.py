from langchain.prompts import SystemMessagePromptTemplate

TEMPLATE = """Given the plan and the function list provided below, please return a JSON object identifying which functions would be most suitable for completing the task, along with reasons for each choice.

The response should only include the JSON object, without any additional explanatory text.

Please provide the recommended functions in the following format:
{{"functions": [{{"name": function_name, "reason": reason_for_recommending }}]}}

Plan:
{user_input}

You may only recommend functions from this Functions List (in JSON format):
{functions_string}
"""
GET_MORE_TOOLS_TEMPLATE = """Given a functions request, the plan and the function list provided below, please return a JSON object identifying which functions would be most suitable for the request, along with reasons for each choice.

The response should only include the JSON object, without any additional explanatory text.

Please provide the recommended functions in the following format:
{{"functions": [{{"name": function_name, "reason": reason_for_recommending }}]}}

Functions Request:
{functions_request}

Plan:
{plan}

You may only recommend functions from this Functions List (in JSON format):
{functions_string}
"""


def initial_selection_template() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(TEMPLATE)


def get_more_tools_template() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(GET_MORE_TOOLS_TEMPLATE)
