import logging

import openai
from langchain.chat_models import ChatOpenAI
from langchain.schema import BaseMessage
from openai import InvalidRequestError

from beebot.body.pack_utils import format_packs_to_openai_functions
from beebot.config.config import FALLBACK_MODEL, Config

logger = logging.getLogger(__name__)


def create_llm(config: Config):
    headers = {}
    if config.openai_api_base:
        openai.api_base = config.openai_api_base
    if config.helicone_key:
        headers["Helicone-Auth"] = f"Bearer {config.helicone_key}"

    llm = ChatOpenAI(
        model_name=config.llm_model,
        model_kwargs={"top_p": 0.2, "headers": headers},
    )
    return llm


def call_llm(
    body: "Body",
    messages: BaseMessage,
    return_function_call: bool = True,
    include_functions: bool = True,
) -> BaseMessage:
    llm = body.llm
    kwargs = {"messages": messages}

    if include_functions:
        kwargs["functions"] = format_packs_to_openai_functions(body.packs)

    if not return_function_call:
        kwargs["function_call"] = "none"

    try:
        response = llm(**kwargs)
    except InvalidRequestError:
        logger.warning(
            f"Model {llm.model_name} is not available. Falling back to {FALLBACK_MODEL}"
        )
        llm.model_name = FALLBACK_MODEL
        response = llm(**kwargs)

    return response
