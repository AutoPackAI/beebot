import json
import logging
from typing import Type

from pydantic import BaseModel, Field

from beebot.body.llm import call_llm
from beebot.body.pack_utils import pack_summaries, all_packs
from beebot.packs.system_base_pack import SystemBasePack
from beebot.prompting.function_selection import get_more_tools_template

PACK_NAME = "get_more_tools"
PACK_DESCRIPTION = "Requests a tool necessary for task fulfillment."

# Just a guess. This should change over time as we learn what coding tasks look like.
CODING_KEYWORDS = [
    "python",
    "code",
    "coding",
    "debug",
    "program",
    "execute",
    "exception",
]

logger = logging.getLogger(__name__)


class GetPacksArgs(BaseModel):
    desired_functionality: str = Field(
        ...,
        description="Express the type of tool that you require in broad terms.",
    )


class GetMoreTools(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = GetPacksArgs

    def _run(self, desired_functionality: str) -> list[str]:
        unfetchable_pack_names = ["exit", "get_more_tools"]
        fetchable_summaries = [
            summary
            for summary in pack_summaries(body=self.body)
            if summary.get("name") not in unfetchable_pack_names
        ]
        prompt = (
            get_more_tools_template()
            .format(
                task=self.body.task,
                plan=self.body.current_plan,
                functions_string=json.dumps(fetchable_summaries),
                functions_request=desired_functionality,
            )
            .content
        )

        response = call_llm(self.body, prompt).text

        functions = [p.strip() for p in response.split(",")]
        packs = all_packs(body=self.body)
        added_packs = []
        for pack_name in functions:
            try:
                pack = packs[pack_name]
                added_packs.append(pack.name)
                self.body.packs[pack_name] = pack
            except Exception as e:
                logger.warning(f"Pack {pack_name} could not be initialized: {e}")

        return f"Functions added: {', '.join(added_packs)}"
