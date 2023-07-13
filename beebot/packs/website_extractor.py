from typing import Callable, Type

from bs4 import BeautifulSoup
from langchain.schema import SystemMessage
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.body import Body
from beebot.body.llm import call_llm
from beebot.body.pack_utils import get_module_path
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "website_extractor"
PACK_DESCRIPTION = "Retrieves and summarizes targeted information from a given URL."
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


def web_extractor(body: Body, url: str, question: str = "") -> str:
    browser = body.playwright.chromium.launch()
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

    response = call_llm(body, [SystemMessage(content=prompt)])
    return response.content


class WebsiteExtractorTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = web_extractor
    args_schema: Type[BaseModel] = Type[WebExtractorArgs]
    body: Body
    return_direct = False

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class WebsiteExtractor(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = WebsiteExtractorTool
    args_schema: Type[BaseModel] = WebExtractorArgs
