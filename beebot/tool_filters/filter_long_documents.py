import json

from langchain.schema import SystemMessage

from beebot.actuator.actuator import ActuatorOutput
from beebot.prompting.summarization import summarization_prompt
from beebot.sensor.sensor import Sensation


def filter_long_documents(
    sphere: "Autosphere", sense: Sensation, output: ActuatorOutput
) -> str:
    response = output.response
    # TODO: Configurable limit or like configurable turn it off?
    if len(response) > 2000:
        summary_prompt = (
            summarization_prompt().format(long_text=response[:8000]).content
        )
        message = SystemMessage(content=summary_prompt)
        summarization = sphere.llm([message])
        response = (
            f"The response was summarized as: {json.dumps(summarization.content)}"
        )

    return response
