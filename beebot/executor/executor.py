import json
import logging
from typing import TYPE_CHECKING

from pydantic import ValidationError

from beebot.decider.decision import Decision
from beebot.executor.observation import Observation

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


class Executor:
    body: "Body"

    def __init__(self, body: "Body"):
        self.body = body

    async def execute(self, decision: Decision) -> Observation:
        """Get pack from tool name. call it"""
        pack = self.body.packs.get(decision.tool_name)
        if not pack:
            import pdb

            pdb.set_trace()
            return Observation(
                success=False,
                error_reason=f"Invalid tool name received: {decision.tool_name}. It may be invalid or may not be "
                f"installed.",
            )

        tool_args = decision.tool_args or {}
        try:
            result = await pack.arun(**tool_args)
            return Observation(response=result)
        except ValidationError as e:
            logger.error(
                f"Error on execution of {decision.tool_name}: {json.dumps(e.errors())}"
            )
            return Observation(response=f"Error: {json.dumps(e.errors())}")
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as e:
            logger.error(f"Error on execution of {decision.tool_name}: {e}")
            return Observation(response=f"Exception: {e}")
