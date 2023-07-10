import json
from json import JSONDecodeError
from typing import TYPE_CHECKING

from beebot.models import Action
from beebot.models.observation import Observation

if TYPE_CHECKING:
    from beebot.body import Body


class Executor:
    body: "Body"

    def __init__(self, body: "Body"):
        self.body = body

    def execute(self, action: Action) -> Observation:
        """Get pack from tool name. call it"""
        try:
            pack = next(
                pack for pack in self.body.packs if pack.name == action.tool_name
            )
        except StopIteration:
            return Observation(
                success=False,
                error_reason=f"Invalid tool name received: {action.tool_name}. It may be invalid or may not be installed.",
            )

        tool_args = action.tool_args or {}
        result = pack.run(tool_input=tool_args)

        try:
            return Observation(response=json.loads(result))
        except JSONDecodeError:
            return Observation(response=result)
