import logging

from pydantic import BaseModel

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "rewind_actions"
PACK_DESCRIPTION = (
    "Reverts the AI assistant's state to the last checkpoint, undoing actions where possible. Note, "
    "actions with irreversible side effects can't be undone."
)

logger = logging.getLogger(__name__)


class RewindActionsArgs(BaseModel):
    pass


class RewindActions(SystemBasePack):
    class Meta:
        name = PACK_NAME

    name = Meta.name
    description = PACK_DESCRIPTION
    args_schema = RewindActionsArgs
    categories = ["System"]

    async def _arun(
        self,
    ) -> str:
        await self.body.rewind()

        return "Rewound successfully"
