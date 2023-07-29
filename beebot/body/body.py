import logging
import os.path
import subprocess
from typing import Optional, Union

from autopack.errors import AutoPackError
from autopack.pack import Pack
from autopack.pack_response import PackResponse
from langchain.chat_models.base import BaseChatModel
from peewee import Database
from pydantic import ValidationError

from beebot.body.body_state_machine import BodyStateMachine
from beebot.body.llm import call_llm, create_llm
from beebot.body.pack_utils import system_packs, get_or_install_pack
from beebot.body.revising_prompt import revise_task_prompt
from beebot.config import Config
from beebot.decider import Decider
from beebot.executor import Executor
from beebot.function_selection.utils import recommend_packs_for_plan
from beebot.memory import Memory
from beebot.memory.memory_chain import MemoryChain
from beebot.models import Decision, Plan
from beebot.models.database_models import initialize_db, BodyModel
from beebot.models.observation import Observation
from beebot.planner import Planner

logger = logging.getLogger(__name__)

RETRY_LIMIT = 3


class Body:
    initial_task: str
    task: str
    current_plan: Plan
    state: BodyStateMachine
    packs: dict[str, "Pack"]
    memories: MemoryChain
    processes: dict[int, subprocess.Popen]

    llm: BaseChatModel
    planner: Planner
    executor: Executor
    decider: Decider
    config: Config

    database: Database = None
    model_object: BodyModel = None

    def __init__(self, initial_task: str = "", config: Config = None):
        self.initial_task = initial_task
        self.task = initial_task
        self.current_plan = Plan(initial_task)
        self.config = config or Config.global_config()
        self.memories = MemoryChain(self)
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
    def from_model(cls, body_model: BodyModel, db: Database = None):
        body = cls(initial_task=body_model.initial_task)
        body.database = db or BodyModel._meta.database
        body.task = body_model.current_task
        body.model_object = body_model

        if body_model.state == BodyStateMachine.setup.value:
            body.setup()
        else:
            body.state.current_state = BodyStateMachine.states_map[body_model.state]

        for chain_model in body_model.memory_chains:
            body.memories = MemoryChain.from_model(body, chain_model)

        body.update_packs(
            [get_or_install_pack(body, pack) for pack in body_model.packs]
        )
        return body

    def setup(self):
        """These are here instead of init because they involve network requests"""
        if self.config.persistence_enabled:
            if not self.database:
                self.database = initialize_db(self.config.database_url)

            if not self.model_object:
                self.model_object = BodyModel(
                    initial_task=self.initial_task, current_task=self.task
                )
                self.model_object.save()

        self.revise_task()
        self.packs = system_packs(self)
        self.update_packs()

        self.state.start()

    def cycle(self) -> Memory:
        """Step through one plan-decide-execute loop"""
        if self.state.current_state == BodyStateMachine.done:
            return

        if self.state.current_state == BodyStateMachine.setup:
            self.setup()

        self.plan()
        self.execute(decision=self.decide())

        complete_memory = self.memories.finish()
        if self.model_object:
            self.model_object.save()
        return complete_memory

    def execute(self, decision: Decision, retry_count: int = 0) -> Observation:
        """Execute a Decision and keep track of state"""
        self.state.execute()
        try:
            result = self.executor.execute(decision=decision)
            self.memories.add_observation(result)
            return result
        except ValidationError as e:
            # It's likely the AI just sent bad arguments, try again.
            logger.warning(
                f"Invalid arguments received: {e}. {decision.tool_name}({decision.tool_args}"
            )
            if retry_count >= RETRY_LIMIT:
                return
            return self.execute(decision, retry_count + 1)
        finally:
            # If the action resulted in status change (e.g. task complete) don't do anything
            if self.state.current_state == self.state.executing:
                self.state.wait()

    def decide(self, plan: Plan = None) -> Decision:
        """Execute an action and keep track of state"""
        self.state.decide()
        plan = plan or self.current_plan

        try:
            decision = self.decider.decide_with_retry(plan=plan)
            self.memories.add_decision(decision)

            return decision
        finally:
            self.state.wait()

    def plan(self):
        """Take the current task and history and develop a plan"""
        self.state.plan()
        try:
            plan = self.planner.plan()
            self.memories.add_plan(plan)
            self.current_plan = plan
            return plan
        finally:
            self.state.wait()

    def revise_task(self):
        """Turn the initial task into a task that is easier for AI to more consistently understand"""
        prompt = revise_task_prompt().format(task=self.initial_task).content
        logger.info("=== Task Revision given to LLM ===")
        logger.info(prompt)

        response = call_llm(self, prompt, include_functions=False).text
        self.task = response

        logger.info("=== Task Revised by LLM ===")
        logger.info(self.task)

    def rewind(self):
        """
        Serves as a control mechanism that allows it to revert its state to a previous checkpoint. The function is
        designed to reverse actions wherever possible and reset the current memories and plan. It should be noted,
        however, that actions with side effects, like sending emails or making API calls, cannot be reversed.
        This is like a jank tree of thought because there's no analysis of the quality of different traversals.
        """
        memories = self.memories.memories
        new_memories = []
        for i in reversed(range(len(memories))):
            if not memories[i].reversible:
                new_memories = memories[: i + 1]

        logger.info(
            f"Rewinding from step {len(memories) + 1} to step {len(new_memories) + 1}"
        )
        # TODO: Create a new chain
        self.memories.memories = new_memories
        self.memories.old_memories = memories

        self.memories.add_plan(Plan(plan_text="Call the rewind_actions function"))

        decision = Decision(
            reasoning="The plan requires that I call the rewind_actions function.",
            tool_name="rewind_actions",
            tool_args="",
        )
        self.memories.add_decision(decision)

        observation = Observation(
            success=True,
            response="You have rewound your state to this point. Please take an unconventional approach this time.",
        )
        self.memories.add_observation(observation)
        self.memories.finish()

    def update_packs(
        self, new_packs: Optional[list[Union[Pack, PackResponse]]] = None
    ) -> list[Pack]:
        if not new_packs:
            new_packs = recommend_packs_for_plan(self)

        for pack in new_packs:
            if pack.name in self.packs:
                continue

            try:
                installed_pack = get_or_install_pack(self, pack.name)
                if not installed_pack:
                    logger.warning(f"Pack {pack.name} could not be installed")

                self.packs[pack.name] = installed_pack

                if installed_pack.depends_on:
                    for dep_name in installed_pack.depends_on:
                        if dep_name in self.packs:
                            continue

                        installed_dep = get_or_install_pack(self, dep_name)
                        if not installed_dep:
                            logger.warning(
                                f"Pack {dep_name}, a dependency of {pack.name} could not be installed"
                            )
                            continue

                        self.packs[dep_name] = installed_dep

            except AutoPackError as e:
                # This is usually because we got a response with a made-up function.
                logger.warning(f"Pack {pack.name} could not be initialized: {e}")
