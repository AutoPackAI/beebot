from typing import Callable, Type

from langchain.schema import HumanMessage
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.body import Body
from beebot.body.llm import call_llm
from beebot.body.pack_utils import get_module_path
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "encyclopedia"
PACK_DESCRIPTION = "A comprehensive factual resource for general knowledge, akin to Wikipedia. Does not provide personalized or up-to-date information. This tool does not provide operational guidance, programming advice, or actionable strategies."


class EncyclopediaArgs(BaseModel):
    query: str = Field(
        ...,
        description="The question to pose.",
    )


def encyclopedia(body: Body, query: str) -> str:
    try:
        # TODO: Maybe a custom prompt?
        response = call_llm(
            body, messages=[HumanMessage(content=query)], return_function_call=False
        )
        return response.content
    except Exception as e:
        return f"Error: {e}"


class EncyclopediaTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = encyclopedia
    args_schema: Type[BaseModel] = Type[EncyclopediaArgs]
    body: Body

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class Encyclopedia(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = EncyclopediaTool
    args_schema: Type[BaseModel] = EncyclopediaArgs
