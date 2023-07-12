import logging
from typing import TYPE_CHECKING

from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage, SystemMessage
from openai import InvalidRequestError

from beebot.packs.utils import format_packs_to_openai_functions
from beebot.prompting import planning_prompt

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)
# IDEAL_MODEL = "gpt-4-0613"
FALLBACK_MODEL = "gpt-3.5-turbo-16k-0613"
IDEAL_MODEL = FALLBACK_MODEL


class Brain:
    body: "Body"
    llm: BaseChatModel

    def __init__(self, body: "Body"):
        self.body = body
        self.llm = ChatOpenAI(model_name=IDEAL_MODEL, model_kwargs={"top_p": 0.2})

    def plan(self, task: str) -> str:
        functions_summary = ", ".join([f"{pack.name}" for pack in self.body.packs])
        formatted_prompt = planning_prompt().format(
            task=task,
            history=self.body.memories.compile_history(),
            functions=functions_summary,
        )
        planned = self.call_llm(
            messages=[SystemMessage(content=formatted_prompt.content)],
        ).content

        logger.info("=== Plan Created ===")
        logger.info(planned)

        return planned

    def call_llm(self, messages: BaseMessage) -> BaseMessage:
        try:
            response = self.llm(
                messages=messages,
                functions=format_packs_to_openai_functions(self.body.packs),
            )
        except InvalidRequestError:
            logger.warning(
                f"Model {self.llm.model_name} is not available. Falling back to {FALLBACK_MODEL}"
            )
            self.llm.model_name = FALLBACK_MODEL
            response = self.llm(
                messages=messages,
                functions=format_packs_to_openai_functions(self.body.packs),
            )

        return response
