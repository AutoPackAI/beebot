import json
import logging
import os
from json import JSONDecodeError
from typing import TYPE_CHECKING

from pydantic import Field, BaseModel

from beebot.body.llm import call_llm
from beebot.config.database_file_manager import IGNORE_FILES
from beebot.decomposer.decomposer_prompt import decomposer_prompt

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from beebot.body import Body


class Subtask(BaseModel):
    agent: str
    instructions: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    complete: bool = False


class Decomposer:
    body: "Body"
    task: str
    subtasks: list[Subtask]

    def __init__(self, body: "Body"):
        self.body = body
        self.task = body.task
        self.subtasks = []

    async def decompose(self) -> list[Subtask]:
        from beebot.agents import BaseAgent

        prompt_template = decomposer_prompt()
        agents = [agent for agent in BaseAgent.__subclasses__() if agent.DESCRIPTION]
        agent_list = "- " + "\n- ".join([agent.DESCRIPTION for agent in agents])
        prompt = prompt_template.format(
            agent_list=agent_list, task=self.task, files=self.starting_files()
        )

        logger.info("\n=== Task Decomposition given to LLM ===")
        logger.info(prompt)

        response = await call_llm(
            self.body,
            prompt,
            include_functions=False,
            function_call="none",
            llm=self.body.decomposer_llm,
        )
        logger.info("\n=== Task Decomposition received from LLM ===")
        logger.info(response.text)

        try:
            parsed_response = json.loads(response.text)
        except JSONDecodeError as e:
            logger.error(f"Could not decode response {e}: {response}")
            # TODO: Handle error better
            raise e

        self.subtasks = [Subtask(**assignment) for assignment in parsed_response]
        return self.subtasks

    def starting_files(self) -> str:
        directory = self.body.config.workspace_path

        file_list = []
        for file in os.listdir(directory):
            abs_path = os.path.abspath(os.path.join(directory, file.replace("/", "_")))
            if not os.path.isdir(abs_path) and file not in IGNORE_FILES:
                file_list.append(f"- {file}")

        if not file_list:
            return ""

        file_list.sort()
        file_list_output = "\n".join(file_list)
        return (
            f"**Files**: Each subtask may have access to any of the following files if included in its inputs:\n"
            f"{file_list_output}"
        )
