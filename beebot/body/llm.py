import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import openai
from autopack.utils import format_packs_to_openai_functions
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage

from beebot.config.config import Config

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from beebot.body import Body


@dataclass
class LLMResponse:
    text: str
    function_call: dict[str, Any]


def create_llm(config: Config, model_name: str):
    headers = {}
    if config.openai_api_base:
        openai.api_base = config.openai_api_base
    if config.helicone_key:
        logger.info("Using helicone to make requests with cache enabled.")
        headers["Helicone-Auth"] = f"Bearer {config.helicone_key}"
        headers["Helicone-Cache-Enabled"] = "true"

    llm = ChatOpenAI(
        model_name=model_name,
        # temperature=0,
        model_kwargs={"headers": headers, "top_p": 0.1},
    )
    return llm


async def call_llm(
    body: "Body",
    message: str,
    function_call: str = "auto",
    include_functions: bool = True,
    disregard_cache: bool = False,
    llm=None,
) -> LLMResponse:
    llm = llm or body.planner_llm
    output_kwargs = {}

    if include_functions and body.current_task_execution.packs:
        output_kwargs["functions"] = format_packs_to_openai_functions(
            body.current_task_execution.packs.values()
        )
        output_kwargs["function_call"] = function_call

    if disregard_cache:
        output_kwargs["headers"] = {"Helicone-Cache-Enabled": "false"}

    logger.debug(f"~~ LLM Request ~~\n{message}")
    response = await llm.agenerate(
        messages=[[SystemMessage(content=message)]], **output_kwargs
    )

    # TODO: This should be a nicer error message if we get an unexpected number of generations
    generation = response.generations[0][0]
    function_called = {}
    if (
        generation
        and hasattr(generation, "message")
        and generation.message.additional_kwargs
    ):
        function_called = generation.message.additional_kwargs.get("function_call", {})

    logger.debug(f"~~ LLM Response ~~\n{generation.text}")
    logger.debug(json.dumps(function_called))
    return LLMResponse(text=generation.text, function_call=function_called)
