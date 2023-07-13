from typing import Type

from langchain.schema import HumanMessage
from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "encyclopedia"
PACK_DESCRIPTION = "A comprehensive factual resource for general knowledge, akin to Wikipedia. Does not provide personalized or up-to-date information. This tool does not provide operational guidance, programming advice, or actionable strategies."


class EncyclopediaArgs(BaseModel):
    query: str = Field(
        ...,
        description="The question to pose.",
    )


class Encyclopedia(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = EncyclopediaArgs

    def _run(self, query: str) -> str:
        try:
            # TODO: Maybe a custom prompt?
            response = self.body.llm(
                messages=[HumanMessage(content=query)], return_function_call=False
            )
            return response.content
        except Exception as e:
            return f"Error: {e}"
