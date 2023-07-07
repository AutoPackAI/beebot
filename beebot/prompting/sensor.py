from langchain.prompts import SystemMessagePromptTemplate

from beebot.prompting.role_prefix import BEEBOT_ROLE_PREFIX

FINISHED_MARKER = "~~~FINISHED~~~"

STARTING_TEMPLATE = """
--- YOUR TASK ---
{task}
--- INSTRUCTIONS ---

Based on your task, make the first action by calling a function. Include no message content in your response. Only call functions that are provided and no other.
"""

REMAINING_TEMPLATE = """
--- YOUR TASK ---
{task}
--- PROGRESS ---
{history}
--- INSTRUCTIONS ---
Your instructions are to execute the action described in Action #{next_action_number}.
"""

PLANNING_TEMPLATE = """
--- YOUR TASK ---
{task}
--- PROGRESS ---
{history}
--- COMPLETION CRITERIA ---
Your task is considered complete if any of the following are true:
    - Every instruction in your task has been completed satisfactorily
    - There are no more actions to take
    - You are repeating actions you have already taken
    - You have gotten errors several times recently and are unsure you if you can continue
--- INSTRUCTIONS ---
Your instructions are to explain the next action you want to do and call a function to do it. This Action should efficiently further your progress in completing your task. In 25 words or less explain why you have taken take this action, and how the previous history has impacted your decision making.

If you you believe you have met at least one completion criteria, do not explain or call a function. Instead, your instructions are to respond with a message that starts with "~~~FINISHED~~~" followed by a detailed summary why you believe you have completed your task and why you are sure that the existing PROGRESS indicates that task has completed, a concise summary of your task, and a concise summary of the success of your functions, including the name of each functions called, in helping you to accomplish your task.
"""


def starting_prompt() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(
        BEEBOT_ROLE_PREFIX + STARTING_TEMPLATE
    )


def remaining_prompt() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(
        BEEBOT_ROLE_PREFIX + REMAINING_TEMPLATE
    )


def planning_prompt() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(
        BEEBOT_ROLE_PREFIX + PLANNING_TEMPLATE
    )
