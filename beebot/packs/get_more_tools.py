import logging
from typing import Callable, Type

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.body import Body
from beebot.packs.system_pack import SystemBasePack
from beebot.packs.utils import get_module_path

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


def run_get_more_tools(body: Body, desired_functionality: str):
    from beebot.packs.utils import suggested_packs

    task = body.initial_task.lower()

    # Don't let it get access to coding/python things unless the task requires it. I can't get the prompt to do it.
    # Perhaps ask the LLM if the task involves coding at the planning stage?
    task_involves_coding = any(keyword in task for keyword in CODING_KEYWORDS)
    request_involves_coding = any(
        keyword in desired_functionality for keyword in CODING_KEYWORDS
    )
    if request_involves_coding and not task_involves_coding:
        return []

    new_packs = suggested_packs(body=body, task=desired_functionality, cache=True)
    initialized_packs = []
    for pack in new_packs:
        try:
            pack.init_tool(init_args=body.get_init_args(pack=pack))
            initialized_packs.append(pack)
        except Exception as e:
            logger.warning(f"Pack {pack.name} could not be initialized: {e}")

    body.packs += initialized_packs[:3]
    new_packs_list = ", ".join([pack.name for pack in initialized_packs[:3]])

    return f"New Packs: {new_packs_list}"


class GetMoreToolsTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = run_get_more_tools
    args_schema: Type[BaseModel] = Type[GetPacksArgs]
    body: Body

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class GetMoreTools(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = GetMoreToolsTool
    args_schema: Type[BaseModel] = GetPacksArgs
