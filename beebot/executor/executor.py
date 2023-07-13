import json
from typing import TYPE_CHECKING

from pydantic import ValidationError

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
        pack = self.body.packs.get(action.tool_name)
        if not pack:
            return Observation(
                success=False,
                error_reason=f"Invalid tool name received: {action.tool_name}. It may be invalid or may not be "
                f"installed.",
            )

        tool_args = action.tool_args or {}
        try:
            result = pack.run(tool_input=tool_args)
            return Observation(response=result)
        except ValidationError as e:
            return Observation(response=f"Error: {json.dumps(e.errors())}")
        except Exception as e:
            return Observation(response=f"Exception: {e}")
