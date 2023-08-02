import logging
import re
from typing import TYPE_CHECKING, Union

from autopack import Pack
from autopack.pack_response import PackResponse
from autopack.utils import functions_bulleted_list

from beebot.body.llm import call_llm
from beebot.body.pack_utils import all_packs
from beebot.function_selection.function_selection_prompt import (
    initial_selection_template,
)

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


async def recommend_packs_for_plan(body: "Body") -> list[Union[Pack, PackResponse]]:
    packs_for_recommendation = [
        pack
        for pack in all_packs(body).values()
        if pack.name not in body.config.auto_include_packs
    ]
    functions_list = functions_bulleted_list(packs_for_recommendation)

    prompt = initial_selection_template().format(
        task=body.task, functions=functions_list
    )
    logger.info("=== Function request sent to LLM ===")
    logger.info(prompt)

    llm_response = await call_llm(body, prompt)
    response = llm_response.text
    logger.info("=== Functions received from LLM ===")
    logger.info(response)

    # Split the response into function names and explanation.
    response_parts = response.split("###")
    # TODO: Do something with the explanation
    function_part, _explanation_part = response_parts

    # Split by commas (if preceded by a word character), and newlines.
    # Remove any arguments given if provided. The prompt says they shouldn't be there, but sometimes they are.
    functions = [
        r.split("(")[0].strip() for r in re.split(r"(?<=\w),|\n", function_part)
    ]

    functions += body.config.auto_include_packs
    packs = all_packs(body)
    return [packs[function] for function in functions if function in packs]
