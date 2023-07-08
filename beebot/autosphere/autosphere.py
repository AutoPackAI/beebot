import json
from logging import Logger
from typing import Any, Union, TYPE_CHECKING

from langchain import WikipediaAPIWrapper
from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_memory import BaseChatMemory
from langchain.requests import TextRequestsWrapper
from langchain.schema import SystemMessage
from playwright.sync_api import Playwright, PlaywrightContextManager
from statemachine import StateMachine, State

from beebot.actuator import Actuator
from beebot.actuator.actuator import ActuatorOutput
from beebot.config import Config
from beebot.packs.utils import gather_packs, system_pack_classes
from beebot.prompting import planning_prompt
from beebot.sensor import Sensor
from beebot.sensor.sensor import SensoryOutput
from beebot.tool_filters import filter_output

if TYPE_CHECKING:
    from autopack.pack import Pack


class AutosphereStateMachine(StateMachine):
    setup = State(initial=True)
    starting = State()
    sensing = State()
    actuating = State()
    waiting = State()
    done = State(final=True)

    start = setup.to(starting)
    sense = actuating.to(sensing) | waiting.to(sensing) | starting.to(sensing)
    actuate = sensing.to(actuating) | waiting.to(actuating)

    wait = actuating.to(waiting) | sensing.to(waiting) | starting.to(waiting)
    finish = waiting.to(done)


class Autosphere:
    initial_task: str
    task: str
    llm: BaseChatModel
    actuator: Actuator
    sensor: Sensor
    config: Config
    state: AutosphereStateMachine
    packs: list["Pack"]
    documents: dict[str, str]
    logger: Logger
    memory: BaseChatMemory
    # This is definitely not the most efficient way, but I want to keep this for our own reference, so we don't go
    # digging through memory all the time, which should be reserved just for AI use.
    cycle_memory: list[tuple[SensoryOutput, ActuatorOutput]]
    playwright: Playwright

    def __init__(self, initial_task: str):
        self.initial_task = initial_task
        self.state = AutosphereStateMachine()
        self.llm = ChatOpenAI(
            temperature=0, model_name="gpt-3.5-turbo-16k-0613", verbose=True
        )
        self.config = Config.from_env()
        self.logger = self.config.custom_logger(__name__)
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        self.cycle_memory = []
        self.sensor = Sensor(sphere=self)
        self.actuator = Actuator(sphere=self)
        self.documents = {}

    def setup(self):
        """These are here instead of init because they involve network requests"""

        self.playwright = PlaywrightContextManager().start()
        self.plan()
        self.packs = gather_packs(sphere=self)

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

        return init_args

    def plan(self):
        formatted_prompt = planning_prompt().format(task=self.initial_task)

        planned_prompt = self.llm(
            messages=[SystemMessage(content=formatted_prompt.content)]
        ).content

        self.task = planned_prompt
        self.logger.info("=== Steps Created ===")
        self.logger.info(self.task)

    # FIXME? this should probably return both the sense and actuation
    def cycle(self) -> Union[ActuatorOutput, SensoryOutput]:
        if self.state.current_state == AutosphereStateMachine.done:
            return

        sensory_output = self.sense()

        if not sensory_output or sensory_output.finished:
            self.state.finish()
            return sensory_output

        actuation_result = self.actuate(sense=sensory_output)
        self.add_chat_memory()
        return actuation_result

    def add_chat_memory(self):
        """Provide a condensed action/result cycle as one chat memory. This helps a lot with keeping messages
        smaller. Putting it all on one line apparently helps the AI too."""
        current_cycle = self.cycle_memory[-1]

        # Don't memorize system calls
        if current_cycle[0].tool_name in [
            klass.__fields__["name"].default for klass in system_pack_classes()
        ]:
            return

        action_str = (
            f"{current_cycle[0].tool_name}({json.dumps(current_cycle[0].tool_args)})"
        )
        result_str = current_cycle[1].compressed()

        chat_memory_string = f"- {action_str}: {result_str}"
        self.memory.chat_memory.add_message(SystemMessage(content=chat_memory_string))

    def actuate(self, sense: SensoryOutput) -> ActuatorOutput:
        self.state.actuate()
        try:
            result = self.actuator.actuate(sense=sense)
            self.add_action_memory(sense=sense, result=result)
            return result
        finally:
            self.state.wait()

    def sense(self) -> SensoryOutput:
        self.state.sense()

        try:
            result = self.sensor.sense()
            self.add_sense_memory(result)
            return result
        finally:
            self.state.wait()

    def add_sense_memory(self, output: SensoryOutput):
        # TODO: Error handling
        self.cycle_memory.append((output,))

    def add_action_memory(self, sense: SensoryOutput, result: ActuatorOutput):
        filtered_output = filter_output(sphere=self, sense=sense, output=result)
        self.cycle_memory[-1] = (self.cycle_memory[-1][0], filtered_output)

    @classmethod
    def init(cls, task: str) -> "Autosphere":
        sphere = Autosphere(initial_task=task)
        sphere.setup()
        return sphere
