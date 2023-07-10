import logging
from typing import TYPE_CHECKING

from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage, SystemMessage

from beebot.packs.utils import format_packs_to_openai_functions
from beebot.prompting import planning_prompt

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


class Brain:
    body: "Body"
    llm: BaseChatModel

    def __init__(self, body: "Body"):
        self.body = body
        self.llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-3.5-turbo-16k-0613",
            model_kwargs={
                "headers": {"Helicone-Auth": f"Bearer {body.config.helicone_key}"},
            },
        )

    def plan(self, task: str) -> str:
        formatted_prompt = planning_prompt().format(task=task)
        planned = self.call_llm(
            messages=[SystemMessage(content=formatted_prompt.content)]
        ).content

        logger.info("=== Plan Created ===")
        logger.info(planned)

        return planned

    def call_llm(self, messages: BaseMessage, retry=False) -> BaseMessage:
        response = self.llm(
            messages=messages,
            functions=format_packs_to_openai_functions(self.body.packs),
        )
        return response
