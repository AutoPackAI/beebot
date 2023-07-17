import logging
from typing import Type

from pydantic import BaseModel

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "rewind_actions"
PACK_DESCRIPTION = "Reverts the AI assistant's state to the last checkpoint, undoing actions where possible. Note, actions with irreversible side effects can't be undone."

logger = logging.getLogger(__name__)


class RewindActionsArgs(BaseModel):
    pass


class RewindActions(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = RewindActionsArgs
    categories: list[str] = ["System"]

    def _run(
        self,
    ) -> str:
        self.body.rewind()

        return "Rewound successfully"
