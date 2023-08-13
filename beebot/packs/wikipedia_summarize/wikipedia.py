import asyncio
import logging
from typing import Union

import wikipedia
from autopack.utils import acall_llm
from pydantic import BaseModel, Field
from wikipedia import WikipediaPage

from beebot.packs.system_base_pack import SystemBasePack

PACK_DESCRIPTION = (
    "Searches Wikipedia based on a question and then analyzes the results. Enables quick access to factual knowledge. "
    "Useful for when you need to answer general questions about people, places, companies, facts, historical events, "
    "or other subjects."
)

PROMPT_TEMPLATE = """Provide an answer to the following question: {question} 

The following Wikipedia pages may also be used for reference:
{pages}
"""

logger = logging.getLogger(__name__)


class WikipediaArgs(BaseModel):
    question_to_ask: str = Field(..., description="A question to ask")


def fetch_page(page_title: str) -> Union[WikipediaPage, None]:
    try:
        return wikipedia.page(title=page_title)
    except BaseException as e:
        logger.warning(f"Could not fetch wikipedia page with title {page_title}: {e}")
        return None


async def get_page(page_title: str) -> WikipediaPage:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, fetch_page, page_title)


async def get_pages(query: str) -> str:
    page_titles = wikipedia.search(query, results=5)
    pages = await asyncio.gather(*(get_page(title) for title in page_titles))

    result = []
    for page in pages:
        if page:
            result.append(f"-- Page: {page.title}\n{page.summary}")

    return "\n".join(result)


class WikipediaPack(SystemBasePack):
    name = "wikipedia"
    description = PACK_DESCRIPTION
    args_schema = WikipediaArgs
    dependencies = ["wikipedia"]
    categories = ["Information"]

    async def _arun(
        self,
        question_to_ask: str,
    ):
        try:
            pages = await get_pages(question_to_ask)
            prompt = PROMPT_TEMPLATE.format(question=question_to_ask, pages=pages)
            response = await acall_llm(prompt, self.allm)
            return response
        except Exception as e:
            return f"Error: {e}"
