import logging
import os.path
import re
import subprocess
from typing import Optional

from autopack.pack import Pack
from langchain.chat_models.base import BaseChatModel
from playwright.sync_api import Playwright, PlaywrightContextManager
from pydantic import ValidationError
from statemachine import StateMachine, State

from beebot.body.llm import call_llm, create_llm
from beebot.body.pack_utils import all_packs, system_packs, functions_bulleted_list
from beebot.body.revising_prompt import revise_task_prompt
from beebot.config import Config
from beebot.decider import Decider
from beebot.executor import Executor
from beebot.memory import Memory
from beebot.memory.memory_storage import MemoryStorage
from beebot.models import Decision, Plan
from beebot.models.observation import Observation
from beebot.packs.function_selection_prompt import initial_selection_template
from beebot.planner import Planner

logger = logging.getLogger(__name__)

RETRY_LIMIT = 3


class BodyStateMachine(StateMachine):
    setup = State(initial=True)
    starting = State()
    planning = State()
    deciding = State()
    executing = State()
    waiting = State()
    done = State(final=True)

    start = setup.to(starting)
    plan = starting.to(planning) | waiting.to(planning)
    decide = waiting.to(deciding)
    execute = waiting.to(executing)
    wait = (
        deciding.to(waiting)
        | planning.to(waiting)
        | executing.to(waiting)
        | starting.to(waiting)
    )
    finish = waiting.to(done) | executing.to(done)


class Body:
    initial_task: str
    task: str
    current_plan: Plan
    state: BodyStateMachine
    packs: dict["Pack"]
    memories: MemoryStorage
    playwright: Playwright
    processes: list[subprocess.Popen]

    llm: BaseChatModel
    planner: Planner
    executor: Executor
    decider: Decider
    config: Config

    def __init__(self, initial_task: str):
        self.initial_task = initial_task
        self.task = initial_task
        self.current_plan = Plan(initial_task)
        self.state = BodyStateMachine()
        self.config = Config.from_env()
        self.memories = MemoryStorage()

        self.llm = create_llm(self.config)
        self.planner = Planner(body=self)
        self.decider = Decider(body=self)
        self.executor = Executor(body=self)
        self.packs = {}
        self.processes = []

        if not os.path.exists(self.config.workspace_path):
            os.makedirs(self.config.workspace_path, exist_ok=True)

    def setup(self):
        """These are here instead of init because they involve network requests"""

        try:
            self.playwright = PlaywrightContextManager().start()
        except Exception as e:
            # TODO: Implement async playwright
            logger.warning(
                f"Playwright could not be started, likely because it needs to be async {e}"
            )

        self.revise_task()
        self.packs = system_packs(self)
        self.update_packs()

        self.state.start()

    def plan(self):
        """Turn the initial task into a plan"""
        self.state.plan()
        try:
            self.current_plan = self.planner.plan()
        finally:
            self.state.wait()

    def cycle(self, retry_count: int = 0) -> Memory:
        """Step through one plan-decide-execute loop"""
        if self.state.current_state == BodyStateMachine.done:
            return

        self.plan()

        self.memories.add_plan(plan=self.plan)

        decision = self.decide()
        self.memories.add_decision(decision=decision)

        try:
            observation = self.execute(decision=decision)
            self.memories.add_observation(observation)
        except ValidationError as e:
            # It's likely the AI just sent bad arguments, try again.
            logger.warning(
                f"Invalid arguments received: {e}. {decision.tool_name}({decision.tool_args}"
            )
            if retry_count >= RETRY_LIMIT:
                return
            return self.cycle(retry_count + 1)

        complete_memory = self.memories.finish()
        return complete_memory

    def execute(self, decision: Decision) -> Observation:
        """Execute a Decision and keep track of state"""
        self.state.execute()
        try:
            result = self.executor.execute(decision=decision)
            return result
        finally:
            # If the action resulted in status change (e.g. task complete) don't do anything
            if self.state.current_state == self.state.executing:
                self.state.wait()

    def decide(self, plan: Plan = None) -> Decision:
        """Execute an action and keep track of state"""
        self.state.decide()
        plan = plan or self.current_plan

        try:
            self.memories.add_plan(plan)
            return self.decider.decide_with_retry(plan=plan)
        finally:
            self.state.wait()

    def recommend_packs_for_current_plan(self) -> list[dict[str, str]]:
        prompt = (
            initial_selection_template()
            .format(
                task=self.task,
                functions_string=functions_bulleted_list(all_packs(self).values()),
            )
            .content
        )
        logger.info("=== Function request sent to LLM ===")
        logger.info(prompt)

        response = call_llm(self, prompt).text
        logger.info("=== Functions received from LLM ===")
        logger.info(response)

        # 1. Split by commas (if preceded by a word character), and newlines.
        # 2. Remove any arguments given if provided. The prompt says they shouldn't be there, but sometimes they are.
        functions = [
            r.split("(")[0].strip() for r in re.split(r"(?<=\w),|\n", response)
        ]
        return functions

    def revise_task(self):
        prompt = revise_task_prompt().format(task=self.initial_task).content
        logger.info("=== Task Revision given to LLM ===")
        logger.info(self.task)
        response = call_llm(self, prompt, include_functions=False).text
        self.task = response
        logger.info("=== Task Revised by LLM ===")
        logger.info(self.task)

    def update_packs(self, new_packs: Optional[list[str]] = None) -> list[Pack]:
        available_packs = all_packs(self)
        if not new_packs:
            new_packs = self.recommend_packs_for_current_plan()

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
