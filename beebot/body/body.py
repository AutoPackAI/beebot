import logging
import os.path
from typing import Any

from autopack.pack import Pack
from langchain import WikipediaAPIWrapper, GoogleSerperAPIWrapper
from langchain.requests import TextRequestsWrapper
from langchain.schema import AIMessage, Memory
from playwright.sync_api import Playwright, PlaywrightContextManager
from statemachine import StateMachine, State

from beebot.brain import Brain
from beebot.brainstem import Brainstem
from beebot.config import Config
from beebot.executor import Executor
from beebot.memory.memory_storage import MemoryStorage
from beebot.models import Action, Stimulus
from beebot.models.observation import Observation
from beebot.packs.system_pack import system_packs
from beebot.sensor import Sensor

logger = logging.getLogger(__name__)


class BodyStateMachine(StateMachine):
    setup = State(initial=True)
    starting = State()
    sensing = State()
    executing = State()
    waiting = State()
    done = State(final=True)

    start = setup.to(starting)
    sense = executing.to(sensing) | waiting.to(sensing) | starting.to(sensing)
    execute = sensing.to(executing) | waiting.to(executing)

    wait = executing.to(waiting) | sensing.to(waiting) | starting.to(waiting)
    finish = waiting.to(done) | executing.to(done)


class Body:
    initial_task: str
    task: str
    state: BodyStateMachine
    packs: list["Pack"]
    memories: MemoryStorage
    playwright: Playwright

    brain: Brain
    brainstem: Brainstem
    executor: Executor
    sensor: Sensor
    config: Config

    def __init__(self, initial_task: str):
        self.initial_task = initial_task
        self.state = BodyStateMachine()
        self.config = Config.from_env()
        self.memories = MemoryStorage()

        self.brain = Brain(body=self)
        self.sensor = Sensor(body=self)
        self.executor = Executor(body=self)
        self.brainstem = Brainstem(body=self)

        if not os.path.exists(self.config.workspace_path):
            os.makedirs(self.config.workspace_path, exist_ok=True)

    def setup(self):
        """These are here instead of init because they involve network requests"""

        self.playwright = PlaywrightContextManager().start()
        self.packs = system_packs(body=self)
        self.plan()

        self.state.start()

    def get_init_args(self, pack: "Pack") -> dict[str, Any]:
        init_args = {}
        for arg_name, init_arg in pack.init_args.items():
            if arg_name == "sync_browser":
                init_args["sync_browser"] = self.playwright.chromium.launch()
            if arg_name == "requests_wrapper":
                init_args["requests_wrapper"] = TextRequestsWrapper()
            if arg_name == "api_wrapper" and pack.name == "Wikipedia":
                init_args["api_wrapper"] = WikipediaAPIWrapper()
            if arg_name == "api_wrapper" and pack.name == "GoogleNewsSearchResultsJSON":
                init_args["api_wrapper"] = GoogleSerperAPIWrapper

        return init_args

    def plan(self):
        """Turn the initial task into a plan"""
        self.task = self.brain.plan(self.initial_task)

    def cycle(self, stimulus: Stimulus = None) -> Memory:
        """Step through one stimulus-action-observation loop"""
        if self.state.current_state == BodyStateMachine.done:
            return

        # If a stimulus was not supplied, generate one from history
        if not stimulus:
            stimulus = Stimulus.generate_stimulus(self)

        self.memories.add_stimulus(stimulus=stimulus)
        brain_output = self.sense(stimulus)

        action = self.brainstem.interpret_brain_output(brain_output)
        self.memories.add_action(action=action)

        observation = self.execute(action=action)
        self.memories.add_observation(observation)

        complete_memory = self.memories.finish()
        return complete_memory

    def execute(self, action: Action) -> Observation:
        """Execute an action and keep track of state"""
        self.state.execute()
        try:
            result = self.executor.execute(action=action)
            return result
        finally:
            # If the action resulted in status change (e.g. task complete) don't do anything
            if self.state.current_state == self.state.executing:
                self.state.wait()

    def sense(self, stimulus: Stimulus) -> AIMessage:
        """Execute an action and keep track of state"""
        self.state.sense()

        try:
            self.memories.add_stimulus(stimulus)
            return self.sensor.sense(stimulus=stimulus)
        finally:
            self.state.wait()
