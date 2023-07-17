import logging
from typing import TYPE_CHECKING

from langchain.chat_models.base import BaseChatModel

from beebot.body.llm import call_llm
from beebot.models import Plan
from beebot.planner.planning_prompt import (
    initial_prompt_template,
    planning_prompt_template,
)
from beebot.utils import list_files, functions_summary

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


class Planner:
    body: "Body"
    llm: BaseChatModel

    def __init__(self, body: "Body"):
        self.body = body

    def plan(self) -> Plan:
        task = self.body.task
        if self.body.memories.memories:
            formatted_prompt = (
                planning_prompt_template()
                .format(
                    task=task,
                    history=self.body.memories.compile_history(),
                    functions=functions_summary(self.body),
                    file_list=", ".join(list_files(self.body)),
                )
                .content
            )
        else:
            formatted_prompt = (
                initial_prompt_template()
                .format(
                    task=task,
                    functions=functions_summary(self.body),
                    file_list=", ".join(list_files(self.body)),
                )
                .content
            )

        response = call_llm(
            self.body,
            message=formatted_prompt,
            function_call="none",
        )
        planned = response

        logger.info("=== Plan Request ===")
        logger.info(formatted_prompt)
        logger.info("=== Plan Created ===")
        logger.info(planned.text)

        return Plan(plan_text=planned.text)
