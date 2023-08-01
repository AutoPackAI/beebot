import logging
from typing import TYPE_CHECKING

from autopack.utils import functions_summary
from langchain.chat_models.base import BaseChatModel

from beebot.body.llm import call_llm
from beebot.models import Plan
from beebot.planner.planning_prompt import (
    initial_prompt_template,
    planning_prompt_template,
)

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
        history = self.body.current_memory_chain.compile_history()
        file_list = self.body.file_manager.document_contents()
        functions = functions_summary(self.body.packs.values())
        prompt_variables = {
            "task": task,
            "history": history,
            "functions": functions,
            "file_list": file_list,
        }
        if history:
            prompt_variables.pop("file_list", None)
            formatted_prompt = planning_prompt_template().format(**prompt_variables)
        else:
            prompt_variables.pop("history", None)
            formatted_prompt = initial_prompt_template().format(
                task=task, functions=functions, file_list=file_list
            )

        logger.info("=== Plan Request ===")
        logger.info(formatted_prompt)

        response = call_llm(
            self.body,
            message=formatted_prompt,
            function_call="none",
        )

        logger.info("=== Plan Created ===")
        logger.info(response.text)

        return Plan(
            prompt_variables=prompt_variables,
            plan_text=response.text,
            response=response.text,
        )
