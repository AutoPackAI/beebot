from typing import Type

from langchain import WikipediaAPIWrapper
from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "wikipedia"
PACK_DESCRIPTION = "Retrieve information from Wikipedia based on a given query. It provides a summary of the relevant Wikipedia page, enabling quick access to factual knowledge."


class WikipediaArgs(BaseModel):
    query: str = Field(
        ...,
        description="The query string to search for on Wikipedia.",
    )


class Wikipedia(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = WikipediaArgs

    def _run(self, query: str) -> list[str]:
        try:
            return [page.page_content for page in WikipediaAPIWrapper().load(query)]
        except Exception as e:
            return f"Error: {e}"
