from langchain.prompts import SystemMessagePromptTemplate

from beebot.prompting.role_prefix import AUTOPACK_ROLE_PREFIX

TEMPLATE = """I will give you a specific task that is input from a human user. Respond with an interpretation of the 
task that will be clearer and more reliably interpreted when used by you in the future. Include intermediate goals in
the response if necessary. Respond only with the interpretation itself and no other content.

--- HUMAN TASK ---
{task}
--- END HUMAN TASK ---

Begin!
"""


def refine_task_prompt() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(AUTOPACK_ROLE_PREFIX + TEMPLATE)
