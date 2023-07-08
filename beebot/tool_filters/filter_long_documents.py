import hashlib

from langchain.schema import SystemMessage

from beebot.actuator.actuator import ActuatorOutput
from beebot.prompting.summarization import summarization_prompt
from beebot.sensor.sensor import Sensation


def filter_long_documents(
    sphere: "Autosphere", sense: Sensation, output: ActuatorOutput
) -> str:
    response = output.response
    # TODO: Configurable limit or like turn it off?
    if len(response) > 1000:
        summary_prompt = (
            summarization_prompt().format(long_text=response[:8000]).content
        )
        message = SystemMessage(content=summary_prompt)
        summarization = sphere.llm([message])
        response = f"The Document was summarized as: {summarization.content}"

    if len(response) > 200:
        # Figure out how to get a readable / meaningful filename
        document_name = hashlib.sha1(response.encode()).hexdigest()[:5] + ".txt"
        sphere.documents[document_name] = response
        return f"See Document Section '{document_name}'"

    return response
