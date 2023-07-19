import logging
import re
from typing import Type

from pydantic import BaseModel, Field

from beebot.body.llm import call_llm
from beebot.body.pack_utils import (
    all_packs,
    functions_bulleted_list,
)
from beebot.function_selection.function_selection_prompt import get_more_tools_template
from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "get_more_tools"
PACK_DESCRIPTION = (
    "Requests a tool necessary for task fulfillment with the given desired functionality, which is a detailed English "
    "sentence. Does not install Python packages. Cannot be used to create tools, functions, or files which do not"
    "already exist."
)

logger = logging.getLogger(__name__)


class GetPacksArgs(BaseModel):
    desired_functionality: str = Field(
        ...,
        description="Specify the desired functionality or purpose of the tool in a detailed sentence.",
    )


class GetMoreTools(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = GetPacksArgs
    categories: list[str] = ["System"]

    def _run(self, desired_functionality: str) -> list[str]:
        packs_to_summarize = [
            pack
            for pack in all_packs(self.body).values()
            if pack.name not in self.body.packs
        ]
        prompt = (
            get_more_tools_template()
            .format(
                task=self.body.task,
                functions=functions_bulleted_list(packs_to_summarize),
                functions_request=desired_functionality,
            )
            .content
        )

        response = call_llm(self.body, prompt, include_functions=False).text

        functions = [r.split("(")[0].strip() for r in re.split(r",|\n", response)]
        all_existing_packs = all_packs(self.body)
        installed_packs = self.body.packs
        added_packs = [
            name
            for name in functions
            if name in all_existing_packs and name not in installed_packs
        ]

        if not added_packs:
            return (
                f"No tools found for '{desired_functionality}'. Do not make another request with the same desired "
                f"functionality."
            )

        self.body.update_packs(added_packs)

        return f"Functions added: {', '.join(added_packs)}"
