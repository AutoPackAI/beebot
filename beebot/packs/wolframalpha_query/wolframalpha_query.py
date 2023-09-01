import os

from autopack import Pack
from langchain import WolframAlphaAPIWrapper
from pydantic import BaseModel, Field

PACK_DESCRIPTION = (
    "Query Wolfram Alpha, a computational knowledge engine, to obtain answers to a wide range of factual and "
    "computational questions. It leverages Wolfram Alpha's extensive knowledge base to provide detailed and accurate "
    "responses. Useful for when you need to answer questions about Math, Science, Technology, and Everyday Life."
)


class WolframAlphaArgs(BaseModel):
    query: str = Field(
        ...,
        description="Specifies the question or topic for which information is sought.",
    )


class WolframAlphaQuery(Pack):
    name = "wolfram_alpha_query"
    description = PACK_DESCRIPTION
    args_schema = WolframAlphaArgs
    dependencies = ["wolframalpha_query"]
    categories = ["Information"]

    def _run(self, query: str) -> list[str]:
        if not os.environ.get("WOLFRAM_ALPHA_APPID"):
            return f"WolframAlpha is not supported as the WOLFRAM_ALPHA_APPID environment variable is not set"

        return WolframAlphaAPIWrapper().run(query)

    async def _arun(self, query: str) -> list[str]:
        return self._run(query)
