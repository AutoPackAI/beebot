from typing import Type

from langchain import WikipediaAPIWrapper
from langchain.schema import SystemMessage
from pydantic import BaseModel, Field

from beebot.body.llm import call_llm
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "wikipedia"
PACK_DESCRIPTION = "Retrieve information from Wikipedia based on a given query. It provides a summary of the relevant Wikipedia page based on a given question, enabling quick access to factual knowledge."

PROMPT_TEMPLATE = """Given the following pages from Wikipedia, provide an answer to the following question:

Question: {question}

Pages:
{pages}
"""


class WikipediaArgs(BaseModel):
    query: str = Field(
        ...,
        description="A search query to pull up pages which may include the answer to your question",
    )
    question: str = Field(
        ...,
        description="The question you wish to answer, posed in the form of a question",
    )


class Wikipedia(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = WikipediaArgs

    def _run(
        self,
        query: str,
        question: str = "Provide me with a general summary of the pages below.",
    ) -> list[str]:
        try:
            page_text = []

            for page in WikipediaAPIWrapper().load(query):
                title = page.metadata.get("title", "Uknown title")
                # Assuming we don't want the summary?
                page_text.append(f"-- Page: {title}\n{page.page_content}")

            prompt = PROMPT_TEMPLATE.format(
                question=question, pages="\n".join(page_text)
            )
            response = call_llm(self.body, [SystemMessage(content=prompt)])
            return response.content

        except Exception as e:
            return f"Error: {e}"
