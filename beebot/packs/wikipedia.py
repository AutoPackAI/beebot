from typing import Callable, Type

from langchain import WikipediaAPIWrapper
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.body import Body
from beebot.body.pack_utils import get_module_path
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "wikipedia"
PACK_DESCRIPTION = "Retrieve information from Wikipedia based on a given query. It provides a summary of the relevant Wikipedia page, enabling quick access to factual knowledge."


class WikipediaArgs(BaseModel):
    query: str = Field(
        ...,
        description="The query string to search for on Wikipedia.",
    )


def wikipedia(body: Body, query: str) -> list[str]:
    try:
        return [page.page_content for page in WikipediaAPIWrapper().load(query)]
    except Exception as e:
        return f"Error: {e}"


class WikipediaTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = wikipedia
    args_schema: Type[BaseModel] = Type[WikipediaArgs]
    body: Body

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class Wikipedia(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = WikipediaTool
    args_schema: Type[BaseModel] = WikipediaArgs
