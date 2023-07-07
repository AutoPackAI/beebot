from langchain.prompts import SystemMessagePromptTemplate

from beebot.prompting.role_prefix import BEEBOT_ROLE_PREFIX

SUMMARIZATION_TEMPLATE = """
--- PREVIOUS HISTORY ---
{history}
--- YOUR TASK ---
{task}
--- INSTRUCTIONS ---

Based on your task and previous history, provide a summary of what has happened so far. Include in your summary how far along you are in completing the task and what remains to be done next. You are your own consumer for this summary, so be sure to include any information you require.
"""


def summarization_prompt() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(
        BEEBOT_ROLE_PREFIX + SUMMARIZATION_TEMPLATE
    )
