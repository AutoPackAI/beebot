import logging
from typing import TYPE_CHECKING

from langchain.schema import BaseMessage
from openai import InvalidRequestError

from beebot.body.pack_utils import format_packs_to_openai_functions
from beebot.config.config import FALLBACK_MODEL

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


def call_llm(
    body: "Body", messages: BaseMessage, return_function_call: bool = True
) -> BaseMessage:
    llm = body.llm
    kwargs = {
        "messages": messages,
        "functions": format_packs_to_openai_functions(body.packs),
    }

    if not return_function_call:
        kwargs["function_call"] = "none"

    try:
        response = llm(**kwargs)
    except InvalidRequestError:
        logger.warning(
            f"Model {llm.model_name} is not available. Falling back to {FALLBACK_MODEL}"
        )
        llm.model_name = FALLBACK_MODEL
        response = llm(
            messages=messages,
            functions=format_packs_to_openai_functions(body.packs),
        )

    return response
