import logging
import os.path
from typing import Any

from autopack.pack import Pack
from langchain import (
    WikipediaAPIWrapper,
    GoogleSerperAPIWrapper,
    GoogleSearchAPIWrapper,
    WolframAlphaAPIWrapper,
    ArxivAPIWrapper,
    SearxSearchWrapper,
)
from langchain.requests import TextRequestsWrapper
from langchain.schema import AIMessage
from langchain.utilities import (
    DuckDuckGoSearchAPIWrapper,
    BingSearchAPIWrapper,
    GraphQLAPIWrapper,
    BraveSearchWrapper,
    PubMedAPIWrapper,
    SceneXplainAPIWrapper,
    ZapierNLAWrapper,
    GooglePlacesAPIWrapper,
    OpenWeatherMapAPIWrapper,
    MetaphorSearchAPIWrapper,
)
from playwright.sync_api import Playwright, PlaywrightContextManager
from pydantic import ValidationError
from statemachine import StateMachine, State

from beebot.brain import Brain
from beebot.brainstem import Brainstem
from beebot.config import Config
from beebot.executor import Executor
from beebot.memory import Memory
from beebot.memory.memory_storage import MemoryStorage
from beebot.models import Action, Stimulus
from beebot.models.observation import Observation
from beebot.packs.system_pack import system_packs
from beebot.packs.utils import gather_packs
from beebot.sensor import Sensor

logger = logging.getLogger(__name__)

RETRY_LIMIT = 3
API_WRAPPERS = {
    "wikipedia": WikipediaAPIWrapper,
    "google_search": GoogleSearchAPIWrapper,
    "google_search_results_json": GoogleSearchAPIWrapper,
    "google_serper": GoogleSerperAPIWrapper,
    "google_serrper_results_json": GoogleSerperAPIWrapper,
    "wolfram_alpha": WolframAlphaAPIWrapper,
    "duckduckgo_results_json": DuckDuckGoSearchAPIWrapper,
    "duckduckgo_search": DuckDuckGoSearchAPIWrapper,
    "bing_search_results_json": BingSearchAPIWrapper,
    "bing_search": BingSearchAPIWrapper,
    "query_graphql": GraphQLAPIWrapper,
    "brave_search": BraveSearchWrapper,
    "arxiv": ArxivAPIWrapper,
    "pubmed": PubMedAPIWrapper,
    "image_explainer": SceneXplainAPIWrapper,
    "zapiernla_list_actions": ZapierNLAWrapper,
    "google_places": GooglePlacesAPIWrapper,
    "searx_search_results": SearxSearchWrapper,
    "searx_search": SearxSearchWrapper,
    "openweathermap": OpenWeatherMapAPIWrapper,
    "metaphor_search_results_json": MetaphorSearchAPIWrapper,
}


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
    current_plan: str
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

            pack_api_wrapper = API_WRAPPERS.get(pack.name)
            if pack_api_wrapper and callable(pack_api_wrapper):
                init_args["api_wrapper"] = pack_api_wrapper()

        return init_args

    def plan(self):
        """Turn the initial task into a plan"""
        self.current_plan = self.brain.plan(self.initial_task)

    def cycle(self, stimulus: Stimulus = None, retry_count: int = 0) -> Memory:
        """Step through one stimulus-action-observation loop"""
        if self.state.current_state == BodyStateMachine.done:
            return

        self.plan()
        gather_packs(self, pack_limit=10)

        # If a stimulus was not supplied, generate one from history
        if not stimulus:
            stimulus = Stimulus.generate_stimulus(self)

        self.memories.add_stimulus(stimulus=stimulus)

        action = self.sense_and_interpretation_with_retry(stimulus)
        self.memories.add_action(action=action)

        try:
            observation = self.execute(action=action)
            self.memories.add_observation(observation)
        except ValidationError as e:
            # It's likely the AI just sent bad arguments, try again.
            logger.warning(
                f"Invalid arguments received: {e}. {action.tool_name}({action.tool_args}"
            )
            if retry_count >= RETRY_LIMIT:
                return
            return self.cycle(stimulus, retry_count + 1)

        complete_memory = self.memories.finish()
        return complete_memory

    def sense_and_interpretation_with_retry(
        self, stimulus: Stimulus, retry_count: int = 0, previous_response: str = ""
    ) -> Action:
        if retry_count and previous_response:
            stimulus.input.content += (
                f"\n\nWarning: You have attempted this next action in the past unsuccessfully. Please reassess your "
                f"strategy. Your failed attempt is: {previous_response}"
            )

        brain_output = self.sense(stimulus)
        try:
            return self.brainstem.interpret_brain_output(brain_output)
        except ValueError:
            logger.warning("Got invalid response from LLM, retrying...")
            if retry_count >= RETRY_LIMIT:
                raise ValueError(f"Got invalid response {RETRY_LIMIT} times in a row")
            return self.sense_and_interpretation_with_retry(
                stimulus, retry_count + 1, previous_response=brain_output.content
            )

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
