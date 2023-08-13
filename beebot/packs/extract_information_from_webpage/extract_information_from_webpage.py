import subprocess

from autopack import Pack
from autopack.utils import call_llm, acall_llm
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright.sync_api import PlaywrightContextManager
from pydantic import BaseModel, Field

PACK_DESCRIPTION = "Extracts specific information from a webpage's content."

PROMPT_TEMPLATE = """Please provide a summary of the following content, which was gathered from the website {url}:
{content}
"""

QUESTION_PROMPT_TEMPLATE = """You are a language model tasked with answering a specific question based on the given content from the website {url}. Please provide an answer to the following question:

Question: {question}

Content:
{content}

Answer:
"""


class ExtractInformationFromWebpageArgs(BaseModel):
    url: str = Field(..., description="The URL of the webpage to analyze.")
    information: str = Field(
        description="The type of information to extract.",
        default="",
    )


class ExtractInformationFromWebpage(Pack):
    name = "extract_information_from_webpage"
    description = PACK_DESCRIPTION
    args_schema = ExtractInformationFromWebpageArgs
    categories = ["Web"]
    dependencies = ["playwright", "beautifulsoup4"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # FIXME: Create an installer type system
        subprocess.run(
            ["playwright", "install"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

    def _run(self, url: str, information: str = "") -> str:
        playwright = PlaywrightContextManager().start()
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()

            page.goto(url)
            html = page.content()
        finally:
            browser.close()
            playwright.stop()

        soup = BeautifulSoup(html, "html.parser")
        body_element = soup.find("body")

        if body_element:
            text = body_element.get_text(separator="\n")[:8000]
        else:
            return "Error: Could not summarize URL."

        if information:
            prompt = QUESTION_PROMPT_TEMPLATE.format(
                content=text, question=information, url=url
            )
        else:
            prompt = PROMPT_TEMPLATE.format(content=text, url=url)

        response = call_llm(prompt, self.llm)
        return response

    async def _arun(self, url: str, information: str = "") -> str:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            page = await browser.new_page()

            await page.goto(url)
            html = await page.content()

        soup = BeautifulSoup(html, "html.parser")
        body_element = soup.find("body")

        if body_element:
            text = body_element.get_text(separator="\n")[:8000]
        else:
            return "Error: Could not summarize URL."

        if information:
            prompt = QUESTION_PROMPT_TEMPLATE.format(
                content=text, question=information, url=url
            )
        else:
            prompt = PROMPT_TEMPLATE.format(content=text, url=url)

        response = await acall_llm(prompt, self.allm)

        return response
