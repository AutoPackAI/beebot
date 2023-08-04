import logging
import os.path
import subprocess
from typing import Optional, Union

import baserun
from autopack.errors import AutoPackError
from autopack.pack import Pack
from autopack.pack_response import PackResponse
from langchain.chat_models.base import BaseChatModel
from pydantic import ValidationError

from beebot.body.body_state_machine import BodyStateMachine
from beebot.body.llm import call_llm, create_llm
from beebot.body.pack_utils import get_or_install_pack
from beebot.body.revising_prompt import revise_task_prompt
from beebot.config import Config
from beebot.config.database_file_manager import DatabaseFileManager
from beebot.decider import Decider
from beebot.execution import Step
from beebot.execution.execution_path import ExecutionPath
from beebot.executor import Executor
from beebot.function_selection.utils import recommend_packs_for_plan
from beebot.models.database_models import (
    BodyModel,
    Plan,
    Decision,
    Observation,
    Oversight,
    initialize_db,
)
from beebot.overseer.overseer import Overseer
from beebot.planner import Planner

logger = logging.getLogger(__name__)

RETRY_LIMIT = 3


class Body:
    initial_task: str
    task: str
    state: BodyStateMachine
    packs: dict[str, "Pack"]
    processes: dict[int, subprocess.Popen]

    llm: BaseChatModel
    overseer: Overseer
    planner: Planner
    executor: Executor
    decider: Decider
    config: Config

    model_object: BodyModel = None
    file_manager: DatabaseFileManager = None
    current_execution_path: ExecutionPath = None

    def __init__(self, initial_task: str = "", config: Config = None):
        self.initial_task = initial_task
        self.task = initial_task
        self.config = config or Config.global_config()
        self.state = BodyStateMachine(self)

        self.llm = create_llm(self.config)
        self.overseer = Overseer(body=self)
        self.planner = Planner(body=self)
        self.decider = Decider(body=self)
        self.executor = Executor(body=self)
        self.packs = {}
        self.processes = {}

        if not os.path.exists(self.config.workspace_path):
            os.makedirs(self.config.workspace_path, exist_ok=True)

    @classmethod
    async def from_model(cls, body_model: BodyModel):
        body = cls(initial_task=body_model.initial_task)
        body.task = body_model.current_task
        body.model_object = body_model
        await body.update_packs()

        body.file_manager = DatabaseFileManager(
            config=body.config.pack_config, body=body
        )

        if body_model.state == BodyStateMachine.setup.value:
            await body.setup()
        else:
            body.state.current_state = BodyStateMachine.states_map[body_model.state]

        for path_model in await body_model.execution_paths.all():
            body.current_execution_path = await ExecutionPath.from_model(
                body, path_model
            )

        await body.setup_file_manager()

        await body.update_packs(
            [get_or_install_pack(body, pack) for pack in body_model.packs]
        )
        return body

    async def setup(self):
        """These are here instead of init because they involve network requests. The order is very specific because
        of when the database and file manager are instantiated / set up"""
        # TODO: Remove duplication between this method and `from_model`
        await initialize_db(self.config.database_url)

        self.current_execution_path = ExecutionPath(self)
        self.file_manager = DatabaseFileManager(
            config=self.config.pack_config, body=self
        )

        if not self.model_object:
            self.model_object = BodyModel(
                initial_task=self.initial_task, current_task=self.task
            )
            await self.save()

        await self.current_execution_path.create_new_step()

        await self.setup_file_manager()
        await self.file_manager.load_from_directory()
        await self.revise_task()
        await self.update_packs()

        await self.create_initial_oversight()
        self.state.oversee()

        await self.save()

    async def cycle(self) -> Step:
        """Step through one decide-execute-plan loop"""
        if self.state.current_state == BodyStateMachine.done:
            return

        if self.state.current_state == BodyStateMachine.setup:
            await self.setup()

        oversight = self.current_execution_path.current_step.oversight

        self.state.decide()
        await self.save()

        decision = await self.decide(oversight)
        await self.execute(decision)

        new_plan = await self.plan()
        await self.current_execution_path.add_plan(new_plan)

        step = await self.current_execution_path.finish()

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

    async def execute(self, decision: Decision, retry_count: int = 0) -> Observation:
        """Execute a Decision and keep track of state"""
        try:
            result = await self.executor.execute(decision=decision)
            await self.current_execution_path.add_observation(result)
            return result
        except ValidationError as e:
            # It's likely the AI just sent bad arguments, try again.
            logger.warning(
                f"Invalid arguments received: {e}. {decision.tool_name}({decision.tool_args}"
            )
            if retry_count >= RETRY_LIMIT:
                return
            return await self.execute(decision, retry_count + 1)
        finally:
            # If the action resulted in status change (e.g. task complete) don't do anything
            if self.state.current_state == self.state.executing:
                self.state.plan()
            await self.save()

    async def decide(self, oversight: Oversight = None) -> Decision:
        """Execute an action and keep track of state"""
        try:
            decision = await self.decider.decide_with_retry(oversight=oversight)
            await self.current_execution_path.add_decision(decision)

            return decision
        finally:
            self.state.execute()
            await self.save()

    async def plan(self) -> Plan:
        """Take the current task and history and develop a plan"""
        try:
            plan = await self.planner.plan()
            await self.current_execution_path.add_plan(plan)
            return plan
        finally:
            if not self.state.current_state == BodyStateMachine.done:
                self.state.oversee()
            await self.save()

    async def create_initial_oversight(self) -> Oversight:
        """Take the current task and history and develop a plan"""
        oversight = await self.overseer.initial_oversight()
        await self.current_execution_path.add_oversight(oversight)
        return oversight

    async def revise_task(self):
        """Turn the initial task into a task that is easier for AI to more consistently understand"""
        prompt = revise_task_prompt().format(task=self.initial_task).content
        logger.info("=== Task Revision given to LLM ===")
        logger.info(prompt)

        llm_response = await call_llm(self, prompt, include_functions=False)
        self.task = llm_response.text

        logger.info("=== Task Revised by LLM ===")
        logger.info(self.task)

    async def rewind(self):
        """
        Serves as a control mechanism that allows it to revert its state to a previous checkpoint. The function is
        designed to reverse actions wherever possible and reset the current steps and plan. It should be noted,
        however, that actions with side effects, like sending emails or making API calls, cannot be reversed.
        This is like a jank tree of thought because there's no analysis of the quality of different traversals.
        """
        steps = self.current_execution_path.steps
        branch_at = 0
        for i in reversed(range(len(steps))):
            if not steps[i].reversible:
                branch_at = i
                break

        logger.info(f"Rewinding from step {len(steps) + 1} to step {branch_at + 1}")

        self.current_execution_path = (
            await self.current_execution_path.create_branch_from(branch_at)
        )

    async def save(self):
        if not self.model_object:
            await self.setup()

        self.model_object.current_task = self.task
        self.model_object.state = self.state.current_state.value
        self.model_object.packs = list(self.packs.keys())
        await self.model_object.save()
        if (
            self.current_execution_path.steps
            and await self.current_execution_path.steps[-1].documents
        ):
            await self.file_manager.flush_to_directory(self.config.workspace_path)

        await self.current_execution_path.save()
        await self.file_manager.flush_to_directory(self.config.workspace_path)

    async def setup_file_manager(self):
        if not self.file_manager:
            self.file_manager = DatabaseFileManager(
                config=self.config.pack_config, body=self
            )
        await self.file_manager.load_from_directory()

        self.config.pack_config.filesystem_manager = self.file_manager

    async def update_packs(
        self, new_packs: Optional[list[Union[Pack, PackResponse]]] = None
    ) -> list[Pack]:
        if not new_packs:
            new_packs = await recommend_packs_for_plan(self)

        pack_names = [pack.name for pack in new_packs]
        pack_names += self.config.auto_include_packs
        for pack_name in pack_names:
            if pack_name in self.packs:
                continue

            try:
                installed_pack = get_or_install_pack(self, pack_name)
                if not installed_pack:
                    logger.warning(f"Pack {pack_name} could not be installed")

                self.packs[pack_name] = installed_pack

                if installed_pack.depends_on:
                    for dep_name in installed_pack.depends_on:
                        if dep_name in self.packs:
                            continue

                        installed_dep = get_or_install_pack(self, dep_name)
                        if not installed_dep:
                            logger.warning(
                                f"Pack {dep_name}, a dependency of {pack_name} could not be installed"
                            )
                            continue

                        self.packs[dep_name] = installed_dep

            except AutoPackError as e:
                # This is usually because we got a response with a made-up function.
                logger.warning(f"Pack {pack_name} could not be initialized: {e}")
