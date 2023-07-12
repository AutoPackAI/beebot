import json
from typing import Callable, Type

from langchain.schema import HumanMessage
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.body import Body
from beebot.packs.system_pack import SystemBasePack
from beebot.packs.utils import get_module_path

PACK_NAME = "encyclopedia"
PACK_DESCRIPTION = (
    "Useful for obtaining factual information on general knowledge topics."
)


class GeneralKnowledgeArgs(BaseModel):
    query: str = Field(
        ...,
        description="The question or statement to pose.",
    )


def general_knowledge(body: Body, query: str):
    try:
        # TODO: Maybe a custom prompt?
        response = body.brain.call_llm(messages=[HumanMessage(content=query)])
        return json.dumps(response.content)
    except Exception as e:
        return f"Error: {e}"


class GeneralKnowledgeTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = general_knowledge
    args_schema: Type[BaseModel] = Type[GeneralKnowledgeArgs]
    body: Body

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class GeneralKnowledge(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = GeneralKnowledgeTool
    args_schema: Type[BaseModel] = GeneralKnowledgeArgs
