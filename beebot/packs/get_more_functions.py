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


def run_get_more_functions(sphere: Autosphere, function_request: str):
    from beebot.packs.utils import suggested_packs

    new_packs = suggested_packs(sphere=sphere, task=function_request, cache=True)
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
