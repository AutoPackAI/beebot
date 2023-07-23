from bs4 import BeautifulSoup
from playwright.sync_api import PlaywrightContextManager
from pydantic import BaseModel, Field

from beebot.body.llm import call_llm
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "analyze_webpage_content"
PACK_DESCRIPTION = (
    "Retrieves and analyzes the content of a given URL, and answers the given question based on the contents of that "
    "webpage"
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


class AnalyzeWebpageContentArgs(BaseModel):
    url: str = Field(
        ..., description="A full and valid URL of the webpage to be analyzed."
    )
    question: str = Field(
        ...,
        description="The question to be answered based on the webpage content.",
    )


class AnalyzeWebpageContent(SystemBasePack):
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = AnalyzeWebpageContentArgs
    categories = ["Web"]

    def _run(self, url: str, question: str = "") -> str:
        playwright = PlaywrightContextManager().start()
        browser = playwright.chromium.launch()
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
