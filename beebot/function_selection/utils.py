import logging
import re
from typing import TYPE_CHECKING, Union

from autopack import Pack
from autopack.pack_response import PackResponse
from autopack.utils import functions_bulleted_list

from beebot.body.llm import call_llm
from beebot.body.pack_utils import all_local_packs, all_packs
from beebot.function_selection.function_selection_prompt import (
    initial_selection_template,
)

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


def recommend_packs_for_plan(body: "Body") -> list[Union[Pack, PackResponse]]:
    prompt = (
        initial_selection_template()
        .format(
            task=body.task,
            functions=functions_bulleted_list(all_local_packs(body).values()),
        )
        .content
    )
    logger.info("=== Function request sent to LLM ===")
    logger.info(prompt)

    response = call_llm(body, prompt).text
    logger.info("=== Functions received from LLM ===")
    logger.info(response)

    # 1. Split by commas (if preceded by a word character), and newlines.
    # 2. Remove any arguments given if provided. The prompt says they shouldn't be there, but sometimes they are.
    functions = [r.split("(")[0].strip() for r in re.split(r"(?<=\w),|\n", response)]
    functions += body.config.auto_include_packs
    packs = all_packs(body)
    return [packs[function] for function in functions]
