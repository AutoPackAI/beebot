from typing import Callable, Type

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.autosphere import Autosphere
from beebot.packs.system_pack import SystemBasePack
from beebot.packs.utils import get_module_path

PACK_NAME = "get_more_functions"
PACK_DESCRIPTION = "Requests a function necessary for task fulfillment."


class GetPacksArgs(BaseModel):
    function_request: str = Field(
        ...,
        description="Express the desired operation or outcome of the function you need in simple, plain English.",
    )


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


def run_get_more_functions(sphere: Autosphere, function_request: str):
    from beebot.packs.utils import suggested_packs

    task = sphere.initial_task.lower()

    # Don't let it get access to coding/python things unless the task requires it. I can't get the prompt to do it.
    # Perhaps ask the LLM if the task involves coding at the planning stage?
    task_involves_coding = any(keyword in task for keyword in CODING_KEYWORDS)
    request_involves_coding = any(
        keyword in function_request for keyword in CODING_KEYWORDS
    )
    if request_involves_coding and not task_involves_coding:
        return []

    new_packs = suggested_packs(sphere=sphere, task=function_request, cache=True)[:3]
    for pack in new_packs:
        try:
            pack.init_tool(init_args=sphere.get_init_args(pack=pack))
        except Exception as e:
            sphere.logger.warning(f"Pack {pack.name} could not be initialized: {e}")

    sphere.packs += new_packs
    new_packs_list = ", ".join([pack.name for pack in new_packs])

    return f"New Packs: {new_packs_list}"


class GetMoreFunctionsTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = run_get_more_functions
    args_schema: Type[BaseModel] = Type[GetPacksArgs]
    sphere: Autosphere

    def _run(self, *args, **kwargs):
        return super()._run(*args, sphere=self.sphere, **kwargs)


class GetMoreFunctions(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = GetMoreFunctionsTool
    args_schema: Type[BaseModel] = GetPacksArgs
