from langchain.prompts import SystemMessagePromptTemplate

TEMPLATE = """
You are a helpful Autonomous AI Agent. I will give you a specific task that is input from a human user. Respond with
an interpretation of the task that will be clearer and more reliably interpreted in the future when used with another
AI system. Do not include any content other than the interpretation.

HUMAN TASK:
{task}
"""


def refine_task_prompt() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(TEMPLATE)
