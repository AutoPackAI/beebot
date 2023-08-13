import logging
import os.path
import subprocess
from typing import Union

import baserun
from langchain.chat_models.base import BaseChatModel

from beebot.body.llm import create_llm
from beebot.config import Config
from beebot.config.database_file_manager import DatabaseFileManager
from beebot.decomposer.decomposer import Decomposer
from beebot.execution import Step
from beebot.execution.task_execution import TaskExecution
from beebot.models.database_models import (
    BodyModel,
    initialize_db,
)

logger = logging.getLogger(__name__)


class Body:
    task: str
    processes: dict[int, subprocess.Popen]
    # Variables set / exported by subtasks
    global_variables: dict[str, str]

    task_executions = list[TaskExecution]

    decomposer_llm: BaseChatModel
    planner_llm: BaseChatModel
    decider_llm: BaseChatModel

    decomposer: Decomposer
    config: Config

    model_object: BodyModel = None
    file_manager: DatabaseFileManager = None

    def __init__(self, task: str = "", config: Config = None):
        self.task = task
        self.config = config or Config.global_config()

        self.decomposer_llm = create_llm(self.config, self.config.decomposer_model)
        self.planner_llm = create_llm(self.config, self.config.planner_model)
        self.decider_llm = create_llm(self.config, self.config.decider_model)
        self.decomposer = Decomposer(body=self)
        self.task_executions = []
        self.processes = {}
        self.global_variables = {}

        if not os.path.exists(self.config.workspace_path):
            os.makedirs(self.config.workspace_path, exist_ok=True)

    @classmethod
    async def from_model(cls, body_model: BodyModel):
        body = cls(task=body_model.task)
        body.model_object = body_model

        body.file_manager = DatabaseFileManager(
            config=body.config.pack_config, body=body
        )

        for execution_model in await body_model.task_executions.all():
            body.task_executions.append(
                await TaskExecution.from_model(body, execution_model)
            )

        await body.setup_file_manager()

        return body

    @property
    def current_task_execution(self) -> Union[TaskExecution, None]:
        try:
            return next(
                execution
                for execution in self.task_executions
                if not execution.complete
            )
        except StopIteration:
            return None

    @property
    def is_done(self):
        return self.current_task_execution is None

    async def setup(self):
        """These are here instead of init because they involve network requests. The order is very specific because
        of when the database and file manager are instantiated / set up"""
        # TODO: Remove duplication between this method and `from_model`
        await initialize_db(self.config.database_url)

        self.file_manager = DatabaseFileManager(
            config=self.config.pack_config, body=self
        )

        await self.decompose_task()

        if not self.model_object:
            self.model_object = BodyModel(task=self.task)
            await self.save()

        await self.current_task_execution.create_new_step()

        await self.setup_file_manager()
        await self.file_manager.load_from_directory()

        await self.save()

    async def cycle(self) -> Step:
        """Step through one decide-execute-plan loop"""
        if self.is_done:
            return

        task_execution = self.current_task_execution
        step = await task_execution.cycle()

        # If this subtask is complete, prime the next subtask
        if task_execution.complete:
            next_execution = self.current_task_execution
            # We're done
            if not next_execution:
                return None

            if not next_execution.current_step:
                await next_execution.create_new_step()

            if next_execution:
                documents = await task_execution.current_step.documents
                for name, document in documents.items():
                    if name in next_execution.inputs:
                        await next_execution.current_step.add_document(document)

        await self.save()

        baserun.log(
            "CycleComplete",
            payload={
                "oversight": step.oversight.__dict__ if step.oversight else None,
                "plan": step.plan.__dict__ if step.plan else None,
                "decision": step.decision.__dict__ if step.decision else None,
                "observation": step.observation.__dict__ if step.observation else None,
            },
        )

        return step

    async def decompose_task(self):
        """Turn the initial task into a task that is easier for AI to more consistently understand"""
        subtasks = await self.decomposer.decompose()
        for subtask in subtasks:
            execution = TaskExecution(
                body=self,
                agent_name=subtask.agent,
                inputs=subtask.inputs,
                outputs=subtask.outputs,
                instructions=subtask.instructions,
                complete=subtask.complete,
            )
            await execution.get_packs()
            self.task_executions.append(execution)

    async def save(self):
        if not self.model_object:
            await self.setup()

        self.model_object.task = self.task
        await self.model_object.save()

        await self.current_task_execution.save()
        await self.file_manager.flush_to_directory(self.config.workspace_path)

    async def setup_file_manager(self):
        if not self.file_manager:
            self.file_manager = DatabaseFileManager(
                config=self.config.pack_config, body=self
            )
        await self.file_manager.load_from_directory()

        self.config.pack_config.filesystem_manager = self.file_manager
