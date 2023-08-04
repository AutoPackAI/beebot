import logging
from typing import TYPE_CHECKING

from autopack.utils import functions_summary

from beebot.body.llm import call_llm
from beebot.models import Oversight
from beebot.planner.planning_prompt import initial_prompt_template

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


class Overseer:
    body: "Body"

    def __init__(self, body: "Body"):
        self.body = body

    async def initial_oversight(self) -> Oversight:
        task = self.body.task
        file_list = await self.body.file_manager.document_contents()
        functions = functions_summary(self.body.packs.values())
        prompt_variables = {
            "task": task,
            "functions": functions,
            "file_list": file_list,
        }
        formatted_prompt = initial_prompt_template().format(**prompt_variables)

        logger.info("=== Initial Plan Request ===")
        logger.info(formatted_prompt)

        response = await call_llm(
            self.body,
            message=formatted_prompt,
            function_call="none",
        )

        logger.info("=== Initial Plan Created ===")
        logger.info(response.text)

        oversight = Oversight(
            prompt_variables=prompt_variables,
            original_plan_text=response.text,
            modified_plan_text=response.text,
            llm_response=response.text,
        )
        await oversight.save()
        return oversight
