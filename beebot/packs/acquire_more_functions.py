import logging
import re

from autopack.get_pack import get_all_pack_info
from autopack.utils import functions_bulleted_list
from pydantic import BaseModel, Field

from beebot.body.llm import call_llm
from beebot.body.pack_utils import (
    all_packs,
)
from beebot.function_selection.function_selection_prompt import (
    acquire_new_functions_template,
)
from beebot.packs.system_base_pack import SystemBasePack

PACK_DESCRIPTION = (
    "Request a general use function that may be helpful for task completion. Does not install Python packages. Cannot "
    "be used to create tools, functions, or files which do not already exist."
)

logger = logging.getLogger(__name__)


class AcquireMoreFunctionsArgs(BaseModel):
    desired_functionality: str = Field(
        ...,
        description="Specify the general functionality or purpose of the function in a detailed sentence.",
    )


class AcquireMoreFunctions(SystemBasePack):
    name = "acquire_new_functions"
    description = PACK_DESCRIPTION
    args_schema = AcquireMoreFunctionsArgs
    categories = ["System"]

    async def _arun(self, desired_functionality: str) -> list[str]:
        existing_functions = ", ".join(self.body.packs.keys())
        prompt = acquire_new_functions_template().format(
            task=self.body.task,
            functions=functions_bulleted_list(all_packs(self.body).values()),
            existing_functions=existing_functions,
            functions_request=desired_functionality,
        )

        llm_response = await call_llm(self.body, prompt, include_functions=False)
        response = llm_response.text

        functions = [r.split("(")[0].strip() for r in re.split(r",|\n", response)]
        packs_by_name = {pack.name: pack for pack in get_all_pack_info()}
        installed_packs = self.body.packs
        added_packs = [
            packs_by_name[name]
            for name in functions
            if name in packs_by_name and name not in installed_packs
        ]

        if not added_packs:
            return (
                f"No tools found for '{desired_functionality}'. Do not make another request with the same desired "
                f"functionality."
            )

        await self.body.update_packs(added_packs)

        return f"Functions added: {', '.join([p.name for p in added_packs])}"
