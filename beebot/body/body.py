import logging
import os.path
import subprocess
from typing import Optional

from autopack.pack import Pack
from langchain.chat_models.base import BaseChatModel
from peewee import Database
from pydantic import ValidationError

from beebot.body.body_state_machine import BodyStateMachine
from beebot.body.llm import call_llm, create_llm
from beebot.body.pack_utils import all_packs, system_packs
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
    packs: dict["Pack"]
    memories: MemoryChain
    processes: list[subprocess.Popen]

    llm: BaseChatModel
    planner: Planner
    executor: Executor
    decider: Decider
    config: Config

    database: Database = None
    database_id: int = None
    database_model: BodyModel = None

    def __init__(self, initial_task: str, database_id: int = None):
        self.initial_task = initial_task
        self.task = initial_task
        self.current_plan = Plan(initial_task)
        self.state = BodyStateMachine(self)
        self.config = Config.from_env()
        self.memories = MemoryChain(self)

        self.llm = create_llm(self.config)
        self.planner = Planner(body=self)
        self.decider = Decider(body=self)
        self.executor = Executor(body=self)
        self.packs = {}
        self.processes = []

        self.database_id = database_id

        if not os.path.exists(self.config.workspace_path):
            os.makedirs(self.config.workspace_path, exist_ok=True)

    def setup(self):
        """These are here instead of init because they involve network requests"""
        if self.config.persistence_enabled:
            self.database = initialize_db(self.config.database_url)
            if self.database_id:
                self.database_model = BodyModel.get_by_id(self.database_id)
            else:
                self.database_model = BodyModel(
                    initial_task=self.initial_task, current_task=self.task
                )
                self.database_model.save()
                self.database_id = self.database_model.id

        self.revise_task()
        self.packs = system_packs(self)
        self.update_packs()

        self.state.start()

    def cycle(self) -> Memory:
        """Step through one plan-decide-execute loop"""
        if self.state.current_state == BodyStateMachine.done:
            return

        self.plan()
        self.execute(decision=self.decide())

        complete_memory = self.memories.finish()
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
        logger.info(self.task)

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
            reasoning=f"The plan requires that I call the rewind_actions function.",
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

    def update_packs(self, new_packs: Optional[list[str]] = None) -> list[Pack]:
        available_packs = all_packs(self)
        if not new_packs:
            new_packs = recommend_packs_for_plan(self)

        for pack_name in new_packs:
            try:
                pack = available_packs[pack_name]
                self.packs[pack_name] = pack
                if pack.depends_on:
                    for dep in pack.depends_on:
                        self.packs[dep] = available_packs[dep]

            except Exception as e:
                # This is usually because we got a response with a made-up function.
                logger.warning(f"Pack {pack_name} could not be initialized: {e}")
