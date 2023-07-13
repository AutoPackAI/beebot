from typing import Callable, Type

from langchain import GoogleSerperAPIWrapper
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.body import Body
from beebot.body.pack_utils import get_module_path
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "google_search"
PACK_DESCRIPTION = (
    "Search Google for websites matching a given query. Useful for when you need to answer questions "
    "about current events."
)


class GoogleSearchArgs(BaseModel):
    query: str = Field(..., description="The query string")


def google_search(body: Body, query: str) -> list[str]:
    try:
        return GoogleSerperAPIWrapper().results(query)
    except Exception as e:
        return f"Error: {e}"


class GoogleSearchTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = google_search
    args_schema: Type[BaseModel] = Type[GoogleSearchArgs]
    body: Body

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class GoogleSearch(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = GoogleSearchTool
    args_schema: Type[BaseModel] = GoogleSearchArgs
