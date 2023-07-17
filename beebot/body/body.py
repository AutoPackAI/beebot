import logging
import os.path
import subprocess
from typing import Optional

from autopack.pack import Pack
from langchain.chat_models.base import BaseChatModel
from pydantic import ValidationError
from statemachine import StateMachine, State

from beebot.body.llm import call_llm, create_llm
from beebot.body.pack_utils import all_packs, system_packs
from beebot.body.revising_prompt import revise_task_prompt
from beebot.config import Config
from beebot.decider import Decider
from beebot.executor import Executor
from beebot.function_selection.utils import recommend_packs_for_plan
from beebot.memory import Memory
from beebot.memory.memory_storage import MemoryStorage
from beebot.models import Decision, Plan
from beebot.models.observation import Observation
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

        # If the tool messed with memories (e.g. rewind) already we don't want to.
        if self.memories.uncompleted_memory.decision is None:
            self.memories.uncompleted_memory = Memory()
            return self.memories.memories[-1]

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

    def revise_task(self):
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
