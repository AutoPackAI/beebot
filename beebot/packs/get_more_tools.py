import json
import logging
from typing import Callable, Type

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.body import Body
from beebot.body.llm import call_llm
from beebot.body.pack_utils import get_module_path, pack_summaries, all_packs
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
        description="Express the desired operation or outcome of the tool you need in simple, plain English.",
    )


def run_get_more_tools(body: Body, desired_functionality: str) -> list[str]:
    unfetchable_pack_names = ["exit", "get_more_tools"]
    fetchable_summaries = [
        summary
        for summary in pack_summaries(body=body)
        if summary.get("name") not in unfetchable_pack_names
    ]
    prompt = get_more_tools_template().format(
        plan=body.current_plan,
        functions_string=json.dumps(fetchable_summaries),
        functions_request=desired_functionality,
    )

    response = call_llm(body, [prompt])

    functions = [p.strip() for p in response.content.split(",")]
    packs = all_packs(body=body)
    added_packs = []
    # This is just returning ['get_more_tools']
    for pack_data in functions:
        pack_name = pack_data.get("name")
        try:
            pack = packs[pack_name]
            added_packs.append(pack.name)
            body.packs[pack_name] = pack
        except Exception as e:
            logger.warning(f"Pack {pack_name} could not be initialized: {e}")

    return added_packs


class GetMoreToolsTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = run_get_more_tools
    args_schema: Type[BaseModel] = Type[GetPacksArgs]
    body: Body

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class GetMoreTools(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = GetMoreToolsTool
    args_schema: Type[BaseModel] = GetPacksArgs
