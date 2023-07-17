from typing import Type

from langchain import WolframAlphaAPIWrapper
from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "wolfram_alpha_query"
PACK_DESCRIPTION = "Query Wolfram Alpha, a computational knowledge engine, to obtain answers to a wide range of factual and computational questions. It leverages Wolfram Alpha's extensive knowledge base to provide detailed and accurate responses."


class WolframAlphaArgs(BaseModel):
    query: str = Field(
        ...,
        description="Specifies the question or topic for which information is sought.",
    )


class WolframAlpha(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = WolframAlphaArgs
    categories: list[str] = ["Information", "Science and Math"]

    def _run(self, query: str) -> list[str]:
        return WolframAlphaAPIWrapper().run(query)
