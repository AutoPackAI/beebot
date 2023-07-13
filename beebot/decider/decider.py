import json
import logging
from typing import TYPE_CHECKING

from langchain.schema import AIMessage

from beebot.body.llm import call_llm
from beebot.models import Stimulus

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


class Decider:
    """
    The Decider is in charge of taking the plan and deciding the next step
    """

    body: "Body"

    def __init__(self, body: "Body"):
        self.body = body

    def decide(self, stimulus: Stimulus) -> AIMessage:
        """Take a stimulus and send it to the Brain (LLM), returning it back to the Body
        TODO: Maybe take in stimulus and not just go off of history"""
        logger.info("=== Sent to LLM ===")
        logger.info(stimulus.input.content)
        logger.info("")
        logger.info(f"Functions provided: {[name for name in self.body.packs.keys()]}")

        response = call_llm(self.body, [stimulus.input])
        logger.info("=== Received from LLM ===")
        logger.info(response.content)
        logger.info("")
        logger.info(f"Function Call: {json.dumps(response.additional_kwargs)}")
        logger.info("")
        return response
