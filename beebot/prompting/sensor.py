from langchain.prompts import SystemMessagePromptTemplate

from beebot.prompting.role_prefix import BEEBOT_ROLE_PREFIX

STARTING_TEMPLATE = """I will give you a specific task that is input from a human user. Determine the first action to 
take by calling a function.

--- ORIGINAL HUMAN TASK ---
{task}
--- END HUMAN TASK ---
"""

REMAINING_TEMPLATE = """Determine the next action to take by calling a function."""


def starting_prompt() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(
        BEEBOT_ROLE_PREFIX + STARTING_TEMPLATE
    )


def remaining_prompt() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(REMAINING_TEMPLATE)
