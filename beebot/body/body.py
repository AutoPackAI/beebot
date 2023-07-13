import json
import logging
import os.path

from autopack.pack import Pack
from langchain import (
    WikipediaAPIWrapper,
    GoogleSerperAPIWrapper,
    GoogleSearchAPIWrapper,
    WolframAlphaAPIWrapper,
    ArxivAPIWrapper,
    SearxSearchWrapper,
)
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

from beebot.body.pack_utils import all_packs, system_packs
from beebot.brain import Brain
from beebot.brainstem import Brainstem
from beebot.config import Config
from beebot.executor import Executor
from beebot.memory import Memory
from beebot.memory.memory_storage import MemoryStorage
from beebot.models import Action, Stimulus
from beebot.models.observation import Observation
from beebot.prompting.function_selection import initial_selection_template
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
    packs: dict["Pack"]
    memories: MemoryStorage
    playwright: Playwright

    brain: Brain
    brainstem: Brainstem
    executor: Executor
    sensor: Sensor
    config: Config

    def __init__(self, initial_task: str):
        self.initial_task = initial_task
        self.current_plan = None
        self.state = BodyStateMachine()
        self.config = Config.from_env()
        self.memories = MemoryStorage()

        self.brain = Brain(body=self)
        self.sensor = Sensor(body=self)
        self.executor = Executor(body=self)
        self.brainstem = Brainstem(body=self)
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
        self.current_plan = self.brain.plan()

    def cycle(self, stimulus: Stimulus = None, retry_count: int = 0) -> Memory:
        """Step through one stimulus-action-observation loop"""
        if self.state.current_state == BodyStateMachine.done:
            return

        self.plan()
        self.update_packs()

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

    def recommend_packs_for_current_plan(self) -> list[dict[str, str]]:
        # TODO: This should probably be mostly, if not entirely, in Brain
        # Use the plan if we have it, otherwise just use the task.
        user_input = self.current_plan or self.initial_task
        functions_string = []
        for pack in all_packs(self).values():
            formatted_args = [
                f"{arg.get('name')}: {arg.get('type')}"
                for arg in pack.run_args.values()
            ]
            functions_string.append(f"{pack.name}({formatted_args})")

        prompt = initial_selection_template().format(
            user_input=user_input, functions_string="\n".join(functions_string)
        )

        response = self.brain.llm([prompt])

        # TODO Handle json errors, perhaps a retry
        try:
            return json.loads(response.content).get("functions")
        except json.JSONDecodeError:
            return []

    def update_packs(self) -> list[Pack]:
        packs = all_packs(self)
        for pack_data in self.recommend_packs_for_current_plan():
            pack_name = pack_data.get("name")
            try:
                pack = packs[pack_name]
                pack.init_tool()
                self.packs[pack_name] = pack
            except Exception as e:
                logger.warning(f"Pack {pack_name} could not be initialized: {e}")
