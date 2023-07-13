from langchain.prompts import SystemMessagePromptTemplate

TEMPLATE = """
As an AI Assistant Efficacy Analyst, your primary responsibility involves evaluating the AI Assistant's task progression, and subsequently updating their plan in accordance with this progress.

Pay close attention to recurring invocations of the same function, as these could signify the AI Assistant encountering a bottleneck. Your updated guidance should aim to effectively navigate the AI Assistant past such hurdles towards task completion.

Presented below is the last prompt given to the AI Assistant. It reflects 

-----------
{prompt}
-----------

Commence your analysis and share your optimized plan.
"""


def revise_plan_prompt() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(TEMPLATE)
