from typing import TYPE_CHECKING

from beebot.body.llm import call_llm
from beebot.packs.summarization_prompt import summarization_prompt_template

if TYPE_CHECKING:
    from beebot.body import Body


async def filter_long_documents(body: "Body", document: str) -> str:
    # TODO: Configurable limit or like configurable turn it off?
    if len(document) > 1000:
        summary_prompt = (
            summarization_prompt_template().format(long_text=document[:8000]).content
        )
        summarization = await call_llm(body, summary_prompt)
        return f"The response was summarized as: {summarization.text}"

    return document
