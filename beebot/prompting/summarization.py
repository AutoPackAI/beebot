from langchain.prompts import SystemMessagePromptTemplate

TEMPLATE = (
    "Summarize the following text, ensuring the final output is no more than 800 characters long. Prioritize key "
    "details such as people, places, and important events:\n\n{long_text}"
)


def summarization_prompt() -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(TEMPLATE)
