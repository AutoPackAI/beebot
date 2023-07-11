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
        for response_line in stimulus.input.content.split("\n"):
            if response_line:
                logger.info(response_line)
        logger.info("")
        try:
            logger.info(f"Functions provided: {[p.tool.name for p in self.body.packs]}")
        except Exception as e:
            print(e)
            import pdb

            pdb.set_trace()

        response = self.body.brain.call_llm([stimulus.input])
        logger.info("=== Received from LLM ===")
        for response_line in response.content.replace("\n\n", "\n").split("\n"):
            if response_line:
                logger.info(response_line)
        logger.info(f"Function Call: {json.dumps(response.additional_kwargs)}")
        return response
