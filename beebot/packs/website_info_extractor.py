from typing import Type

from bs4 import BeautifulSoup
from langchain.schema import SystemMessage
from pydantic import BaseModel, Field

from beebot.body.llm import call_llm
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "website_info_extractor"
PACK_DESCRIPTION = (
    "Retrieves data from a specified URL and creates a concise summary based on a given query. It navigates "
    "the webpage, identifies relevant information, and synthesizes it into a useful and understandable response, "
    "allowing the AI Assistant to gain targeted insights from web content."
)
PROMPT_TEMPLATE = """Please provide a summary of the following content, which was gathered from the website {url}:
{content}
"""

QUESTION_PROMPT_TEMPLATE = """You are a language model tasked with answering a specific question based on the given content from the website {url}. Please provide a concise answer to the following question:

Question: {question}

Content:
{content}

Answer:
"""


class WebExtractorArgs(BaseModel):
    url: str = Field(..., description="The web address to extract information from")
    question: str = Field(
        ...,
        description="A detailed description of the desired information to be retrieved in the form of a question.",
    )


class WebsiteExtractor(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = WebExtractorArgs

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

        response = call_llm(self.body, [SystemMessage(content=prompt)])
        return response.content
