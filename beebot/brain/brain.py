import logging
from typing import TYPE_CHECKING

from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage
from openai import InvalidRequestError

from beebot.body.pack_utils import format_packs_to_openai_functions
from beebot.prompting import planning_prompt
from beebot.prompting.planning import initial_prompt
from beebot.utils import list_files

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

    def plan(self) -> str:
        task = self.body.initial_task
        functions_summary = ", ".join([f"{name}" for name in self.body.packs.keys()])
        if self.body.memories.memories:
            formatted_prompt = planning_prompt().format(
                task=task,
                history=self.body.memories.compile_history(),
                functions=functions_summary,
                file_list=", ".join(list_files(self.body)),
            )
        else:
            formatted_prompt = initial_prompt().format(
                task=task,
                functions=functions_summary,
                file_list=", ".join(list_files(self.body)),
            )

        response = self.call_llm(
            messages=[formatted_prompt],
            return_function_call=False,
        )
        planned = response.content

        logger.info("=== Plan Request ===")
        logger.info(formatted_prompt.content)
        logger.info("=== Plan Created ===")
        logger.info(planned)

        return planned

    def call_llm(
        self, messages: BaseMessage, return_function_call: bool = True
    ) -> BaseMessage:
        kwargs = {
            "messages": messages,
            "functions": format_packs_to_openai_functions(self.body.packs),
        }

        if not return_function_call:
            kwargs["function_call"] = "none"

        try:
            response = self.llm(**kwargs)
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
