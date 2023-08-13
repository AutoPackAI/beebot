import json
import logging
from typing import TYPE_CHECKING

from pydantic import ValidationError

from beebot.models.database_models import Decision, Observation

if TYPE_CHECKING:
    from beebot.execution.task_execution import TaskExecution

logger = logging.getLogger(__name__)


class Executor:
    def __init__(self, task_execution: "TaskExecution"):
        self.task_execution = task_execution

    async def execute(self, decision: Decision) -> Observation:
        """Get pack from tool name. call it"""
        pack = self.task_execution.packs.get(decision.tool_name)
        if not pack:
            return Observation(
                success=False,
                error_reason=f"Invalid tool name received: {decision.tool_name}. It may be invalid or may not be "
                f"installed.",
            )

        tool_args = decision.tool_args or {}
        try:
            result = await pack.arun(**tool_args)
            logger.info("\n=== Execution observation ===")
            logger.info(result)
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
            return Observation(
                response=f"Exception: {e}",
                success=False,
                # TODO: Improve error_reason
                error_reason=str(e),
            )
