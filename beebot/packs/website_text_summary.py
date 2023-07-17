from typing import Type

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from beebot.body.llm import call_llm
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "website_text_summary"
PACK_DESCRIPTION = (
    "Extracts text content from a specified website URL and generates a summary based on a provided "
    "question."
)

PROMPT_TEMPLATE = """Please provide a summary of the following content, which was gathered from the website {url}:
{content}
"""

QUESTION_PROMPT_TEMPLATE = """You are a language model tasked with answering a specific question based on the given content from the website {url}. Please provide an answer to the following question:

Question: {question}

Content:
{content}

Answer:
"""


class WebsiteTextSummaryArgs(BaseModel):
    url: str = Field(
        ..., description="The URL of the website to be accessed and extracted."
    )
    question: str = Field(
        description="The question or query used to generate a summary of the extracted text content.",
    )


class WebsiteTextSummary(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = WebsiteTextSummaryArgs
    categories: list[str] = ["Web"]

    def _run(self, url: str, question: str = "") -> str:
        browser = self.body.playwright.chromium.launch()
        page = browser.new_page()

        page.goto(url)
        html = page.content()
        browser.close()

        soup = BeautifulSoup(html, "html.parser")
        body_element = soup.find("body")

        if body_element:
            text = body_element.get_text(separator="\n")
        else:
            return "Error: Could not summarize URL."

        if question:
            prompt = QUESTION_PROMPT_TEMPLATE.format(
                content=text, question=question, url=url
            )
        else:
            prompt = PROMPT_TEMPLATE.format(content=text, url=url)

        response = call_llm(self.body, prompt, include_functions=False).text
        return response
