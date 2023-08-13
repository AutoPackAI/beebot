import logging
from typing import TYPE_CHECKING

from langchain.chat_models.base import BaseChatModel

from beebot.body.llm import call_llm
from beebot.models.database_models import Plan

if TYPE_CHECKING:
    from beebot.execution.task_execution import TaskExecution

logger = logging.getLogger(__name__)


class Planner:
    llm: BaseChatModel

    task_execution: "TaskExecution"

    def __init__(self, task_execution: "TaskExecution"):
        self.task_execution = task_execution

    async def plan(self) -> Plan:
        prompt, prompt_variables = await self.task_execution.agent.planning_prompt()

        logger.info("\n=== Plan Request ===")
        logger.info(prompt)

        response = await call_llm(
            self.task_execution.body,
            message=prompt,
            function_call="none",
            include_functions=True,
        )

        logger.info("\n=== Plan Created ===")
        logger.info(response.text)

        plan = Plan(
            prompt_variables=prompt_variables,
            plan_text=response.text,
            llm_response=response.text,
        )
        await plan.save()
        return plan
