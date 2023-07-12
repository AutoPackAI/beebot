import json
import logging
from typing import TYPE_CHECKING

from langchain.schema import AIMessage

from beebot.models import Stimulus

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


class Sensor:
    """
    A Sensor is in charge of taking sensory input from the Body, sending it to the LLM, then returning the response
    back to the Body
    """

    body: "Body"

    def __init__(self, body: "Body"):
        self.body = body

    def sense(self, stimulus: Stimulus) -> AIMessage:
        """Take a stimulus and send it to the Brain (LLM), returning it back to the Body
        TODO: Maybe take in stimulus and not just go off of history"""
        logger.info("=== Sent to LLM ===")
        logger.info(stimulus.input.content)
        logger.info("")
        logger.info(f"Functions provided: {[p.tool.name for p in self.body.packs]}")

        response = self.body.brain.call_llm([stimulus.input])
        logger.info("=== Received from LLM ===")
        logger.info(response.content)
        logger.info("")
        logger.info(f"Function Call: {json.dumps(response.additional_kwargs)}")
        logger.info("")
        return response
