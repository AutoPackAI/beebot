import logging
import os.path

from autopack.pack import Pack
from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from playwright.sync_api import Playwright, PlaywrightContextManager
from pydantic import ValidationError
from statemachine import StateMachine, State

from beebot.body.llm import call_llm
from beebot.body.pack_utils import all_packs, system_packs
from beebot.config import Config
from beebot.config.config import IDEAL_MODEL
from beebot.decider import Decider
from beebot.executor import Executor
from beebot.memory import Memory
from beebot.memory.memory_storage import MemoryStorage
from beebot.models import Decision, Plan
from beebot.models.observation import Observation
from beebot.planner import Planner
from beebot.prompting.function_selection import initial_selection_template

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
    current_plan: Plan
    state: BodyStateMachine
    packs: dict["Pack"]
    memories: MemoryStorage
    playwright: Playwright

    llm: BaseChatModel
    planner: Planner
    executor: Executor
    decider: Decider
    config: Config

    def __init__(self, initial_task: str):
        self.initial_task = initial_task
        self.current_plan = Plan(initial_task)
        self.state = BodyStateMachine()
        self.config = Config.from_env()
        self.memories = MemoryStorage()

        self.llm = ChatOpenAI(model_name=IDEAL_MODEL, model_kwargs={"top_p": 0.2})
        self.planner = Planner(body=self)
        self.decider = Decider(body=self)
        self.executor = Executor(body=self)
        self.packs = {}

        if not os.path.exists(self.config.workspace_path):
            os.makedirs(self.config.workspace_path, exist_ok=True)

    def setup(self):
        """These are here instead of init because they involve network requests"""

        self.playwright = PlaywrightContextManager().start()
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
        self.update_packs()

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
        # TODO: This should probably be mostly, if not entirely, in Brain
        # Use the plan if we have it, otherwise just use the task.
        user_input = self.current_plan or self.initial_task
        functions_string = []
        for pack in all_packs(self).values():
            formatted_args = ", ".join(
                [
                    f"{arg.get('name')}: {arg.get('type')}"
                    for arg in pack.run_args.values()
                ]
            )
            functions_string.append(f"{pack.name}({formatted_args})")

        prompt = initial_selection_template().format(
            user_input=user_input, functions_string="\n".join(functions_string)
        )

        response = call_llm(self, [prompt])

        return [p.strip() for p in response.content.split(",")]

    def update_packs(self) -> list[Pack]:
        available_packs = all_packs(self)
        for pack_name in self.recommend_packs_for_current_plan():
            try:
                pack = available_packs[pack_name]
                self.packs[pack_name] = pack
            except Exception as e:
                logger.warning(f"Pack {pack_name} could not be initialized: {e}")
