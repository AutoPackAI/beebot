from pydantic import BaseModel, Field

from beebot.body.llm import call_llm
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "encyclopedia"
PACK_DESCRIPTION = (
    "The best comprehensive factual resource for general knowledge. Does not provide personalized or "
    "or real-time data. This tool does not provide operational guidance, programming advice, "
    "or actionable strategies."
)


class EncyclopediaArgs(BaseModel):
    query: str = Field(
        ...,
        description="The question to pose.",
    )


class Encyclopedia(SystemBasePack):
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = EncyclopediaArgs
    categories = ["Information", "Science and Math"]

    async def _arun(self, query: str) -> str:
        try:
            # TODO: Maybe a custom prompt?
            llm_response = await call_llm(
                body=self.body,
                message=query,
                function_call="none",
            )

            return llm_response.text
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as e:
            return f"Error: {e}"
