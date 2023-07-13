import json
from typing import TYPE_CHECKING

from langchain.schema import SystemMessage

from beebot.body.llm import call_llm
from beebot.models import Action
from beebot.models.observation import Observation
from beebot.models.stimulus import Stimulus
from beebot.prompting.summarization import summarization_prompt

if TYPE_CHECKING:
    from beebot.body import Body


def filter_long_documents(
    body: "Body", stimulus: Stimulus, action: Action, observation: Observation
) -> str:
    response = observation.response
    # TODO: Configurable limit or like configurable turn it off?
    if len(response) > 2000:
        summary_prompt = (
            summarization_prompt().format(long_text=response[:8000]).content
        )
        message = SystemMessage(content=summary_prompt)
        summarization = call_llm(body, [message])
        response = (
            f"The response was summarized as: {json.dumps(summarization.content)}"
        )

    return response
