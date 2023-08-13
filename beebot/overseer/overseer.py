import logging
from typing import TYPE_CHECKING

from beebot.body.llm import call_llm
from beebot.models import Oversight

if TYPE_CHECKING:
    from beebot.execution.task_execution import TaskExecution

logger = logging.getLogger(__name__)


class Overseer:
    """This doesn't really do anything right now, but in the future this will be where the human has a chance to modify
    plans from the previous step before executing this step"""

    task_execution: "TaskExecution"

    def __init__(self, task_execution: "TaskExecution"):
        self.task_execution = task_execution

    async def initial_oversight(self) -> Oversight:
        logger.info("\n=== Initial Plan Request ===")
        (
            prompt,
            prompt_variables,
        ) = await self.task_execution.agent.planning_prompt()
        logger.info(prompt)

        response = await call_llm(
            self.task_execution.body,
            message=prompt,
            function_call="none",
        )

        logger.info("\n=== Initial Plan Created ===")
        logger.info(response.text)

        oversight = Oversight(
            prompt_variables=prompt_variables,
            original_plan_text=response.text,
            modified_plan_text=response.text,
            llm_response=response.text,
        )
        await oversight.save()
        return oversight
