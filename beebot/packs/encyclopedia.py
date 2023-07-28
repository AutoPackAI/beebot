from pydantic import BaseModel, Field

from beebot.body.llm import call_llm
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "encyclopedia"
PACK_DESCRIPTION = (
    "The best comprehensive factual resource for general knowledge. Does not provide personalized or "
    "information from the two past years. This tool does not provide operational guidance, programming advice, "
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
    categories = ["Information"]

    def _run(self, query: str) -> str:
        try:
            # TODO: Maybe a custom prompt?
            response = call_llm(
                body=self.body,
                message=query,
                function_call="none",
            ).text

            return response
        except Exception as e:
            return f"Error: {e}"
