import baserun
import logging
import os.path
import subprocess
from typing import Optional, Union

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
from beebot.decider.decision import Decision
from beebot.executor import Executor
from beebot.executor.observation import Observation
from beebot.function_selection.utils import recommend_packs_for_plan
from beebot.memory import Memory
from beebot.memory.memory_chain import MemoryChain
from beebot.models.database_models import BodyModel
from beebot.planner import Planner
from beebot.planner.plan import Plan

logger = logging.getLogger(__name__)

RETRY_LIMIT = 3


class Body:
    initial_task: str
    task: str
    state: BodyStateMachine
    packs: dict[str, "Pack"]
    processes: dict[int, subprocess.Popen]

    llm: BaseChatModel
    planner: Planner
    executor: Executor
    decider: Decider
    config: Config

    current_plan: Plan = None
    model_object: BodyModel = None
    file_manager: DatabaseFileManager = None
    current_memory_chain: MemoryChain = None

    def __init__(self, initial_task: str = "", config: Config = None):
        self.initial_task = initial_task
        self.task = initial_task
        self.config = config or Config.global_config()
        self.state = BodyStateMachine(self)

        self.llm = create_llm(self.config)
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

        if body_model.state == BodyStateMachine.setup.value:
            await body.setup()
        else:
            body.state.current_state = BodyStateMachine.states_map[body_model.state]

        for chain_model in await body_model.memory_chains:
            body.current_memory_chain = MemoryChain.from_model(body, chain_model)

        await body.update_packs(
            [get_or_install_pack(body, pack) for pack in body_model.packs]
        )
        return body

    async def setup(self):
        """These are here instead of init because they involve network requests. The order is very specific because
        of when the database and file manager are instantiated / set up"""
        self.current_memory_chain = MemoryChain(self)
        self.file_manager = DatabaseFileManager(
            config=self.config.pack_config, body=self
        )

        if not self.model_object:
            self.model_object = BodyModel(
                initial_task=self.initial_task, current_task=self.task
            )
            await self.save()

        await self.current_memory_chain.create_incomplete_memory()

        await self.setup_file_manager()
        await self.file_manager.load_from_directory()
        await self.revise_task()
        await self.update_packs()

        self.state.start()
        await self.save()

    async def cycle(self) -> Memory:
        """Step through one plan-decide-execute loop"""
        if self.state.current_state == BodyStateMachine.done:
            return

        if self.state.current_state == BodyStateMachine.setup:
            await self.setup()

        await self.plan()
        await self.execute(decision=await self.decide())

        complete_memory = await self.current_memory_chain.finish()
        await self.save()

        baserun.log("CycleComplete", payload={
            "plan": complete_memory.plan.__dict__ if complete_memory.plan else None,
            "decision": complete_memory.decision.__dict__ if complete_memory.decision else None,
            "observation": complete_memory.observation.__dict__ if complete_memory.observation else None,
        })

        return complete_memory

    async def execute(self, decision: Decision, retry_count: int = 0) -> Observation:
        """Execute a Decision and keep track of state"""
        self.state.execute()
        await self.save()
        try:
            result = await self.executor.execute(decision=decision)
            await self.current_memory_chain.add_observation(result)
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
                self.state.wait()
            await self.save()

    async def decide(self, plan: Plan = None) -> Decision:
        """Execute an action and keep track of state"""
        self.state.decide()
        await self.save()
        plan = plan or self.current_plan

        try:
            decision = await self.decider.decide_with_retry(plan=plan)
            await self.current_memory_chain.add_decision(decision)

            return decision
        finally:
            self.state.wait()
            await self.save()

    async def plan(self):
        """Take the current task and history and develop a plan"""
        self.state.plan()
        await self.save()
        try:
            plan = await self.planner.plan()
            await self.current_memory_chain.add_plan(plan)
            self.current_plan = plan
            return plan
        finally:
            self.state.wait()
            await self.save()

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
        designed to reverse actions wherever possible and reset the current memories and plan. It should be noted,
        however, that actions with side effects, like sending emails or making API calls, cannot be reversed.
        This is like a jank tree of thought because there's no analysis of the quality of different traversals.
        # TODO: Extract this to some sort of memory manager
        """
        memories = self.current_memory_chain.memories
        new_memories = []
        for i in reversed(range(len(memories))):
            if not memories[i].reversible:
                new_memories = memories[: i + 1]

        logger.info(
            f"Rewinding from step {len(memories) + 1} to step {len(new_memories) + 1}"
        )
        # TODO: Create a new chain
        self.current_memory_chain.memories = new_memories
        self.current_memory_chain.old_memories = memories

        await self.current_memory_chain.add_plan(
            Plan(plan_text="Call the rewind_actions function")
        )

        decision = Decision(
            reasoning="The plan requires that I call the rewind_actions function.",
            tool_name="rewind_actions",
            tool_args="",
        )
        await self.current_memory_chain.add_decision(decision)

        observation = Observation(
            success=True,
            response="You have rewound your state to this point. Please take an unconventional approach this time.",
        )
        await self.current_memory_chain.add_observation(observation)
        await self.current_memory_chain.finish()

    async def save(self):
        if not self.model_object:
            await self.setup()

        self.model_object.current_task = self.task
        self.model_object.state = self.state.current_state.value
        self.model_object.packs = list(self.packs.keys())
        await self.model_object.save()
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
