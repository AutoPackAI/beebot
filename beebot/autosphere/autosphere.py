import json
import os
import traceback
from json import JSONDecodeError
from logging import Logger
from typing import Any, Union

import langchain
from autopack.get_pack import try_get_pack
from autopack.installation import install_pack
from autopack.pack import Pack
from autopack.selection import select_packs
from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_memory import BaseChatMemory
from langchain.requests import TextRequestsWrapper
from playwright.sync_api import Playwright, PlaywrightContextManager
from statemachine import StateMachine, State

from beebot.actuator import Actuator
from beebot.actuator.actuator import ActuatorOutput
from beebot.config import Config
from beebot.prompting import refine_task_prompt
from beebot.sensor import Sensor
from beebot.sensor.sensor import SensoryOutput


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
    packs: list[Pack]
    logger: Logger
    memory: BaseChatMemory
    playwright: Playwright

    def __init__(self, initial_task: str):
        """Set only the initial task. The rest of the fields are set during `setup`. This is because we don't want to
        make network requests on __init__ (it makes it difficult to test)."""
        self.initial_task = initial_task
        self.state = AutosphereStateMachine()

    def setup(self):
        langchain.debug = True

        self.llm = ChatOpenAI(
            temperature=0, model_name="gpt-3.5-turbo-16k-0613", verbose=True
        )
        self.config = Config.from_env()
        self.logger = self.config.custom_logger(__name__)
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        self.playwright = PlaywrightContextManager().start()
        self.refine_task()
        self.gather_packs()
        self.sensor = Sensor(sphere=self)
        self.actuator = Actuator(sphere=self)

        self.state.start()

    def gather_packs(self):
        cache_path = ".autopack/selection_cache.json"
        pack_ids = []
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                cached_results = json.load(f)
            if self.initial_task in cached_results:
                pack_ids = cached_results.get(self.initial_task)

        if not pack_ids:
            self.logger.info("Selecting packs")
            pack_ids = select_packs(self.task, self.llm)
            self.logger.info(f"Packs selected: {pack_ids}")

        packs = []
        for pack_id in pack_ids:
            pack = try_get_pack(pack_id, quiet=False)

            if pack:
                packs.append(pack)
                continue

            if self.config.auto_install_packs:
                self.logger.info(f"Installing pack {pack_id}")
                try:
                    pack = install_pack(
                        pack_id,
                        force_dependencies=self.config.auto_install_dependencies,
                    )
                except Exception as e:
                    import pdb

                    pdb.set_trace()
                    print(traceback.format_exception(e))
                    raise e

                if pack:
                    packs.append(pack)
                else:
                    self.logger.warning(f"Pack {pack_id} could not be installed")
                    continue

            else:
                self.logger.warning(f"Pack {pack_id} is not installed")
                continue

        for pack in packs:
            try:
                init_args = self.get_init_args(pack=pack)
                pack.init_tool(init_args=init_args)
            except:
                import pdb

                pdb.set_trace()

        self.packs = packs
        used_pack_ids = [pack.pack_id for pack in packs]
        self.logger.info(f"Packs used: {used_pack_ids}")

        os.path.abspath(cache_path)
        with open(cache_path, "w+") as f:
            try:
                existing_cache = json.load(f)
            except JSONDecodeError:
                existing_cache = {}

            existing_cache[self.initial_task] = used_pack_ids
            json.dump(existing_cache, f)

        return self.packs

    def get_init_args(self, pack: Pack) -> dict[str, Any]:
        init_args = {}
        for arg_name, init_arg in pack.init_args.items():
            if arg_name == "sync_browser":
                init_args["sync_browser"] = self.playwright.chromium.launch()
            if arg_name == "requests_wrapper":
                init_args["requests_wrapper"] = TextRequestsWrapper()

        return init_args

    def refine_task(self):
        refine_prompt = refine_task_prompt()
        formatted_prompt = refine_prompt.format(task=self.initial_task)

        refined = self.llm([formatted_prompt])
        content = refined.content
        if content.startswith("Interpretation:"):
            content = content.replace("Interpretation:", "")

        self.task = content
        self.logger.info(self.task)

    def cycle(self) -> Union[ActuatorOutput, SensoryOutput]:
        if self.state.current_state == AutosphereStateMachine.done:
            return

        if self.state.current_state == AutosphereStateMachine.starting:
            self.state.sense()
            try:
                sensory_output = self.sensor.start()
            finally:
                self.state.wait()
        else:
            sensory_output = self.sense()

        if not sensory_output or sensory_output.finished:
            self.state.finish()
            return sensory_output

        return self.actuate(sensory_output.tool, sensory_output.tool_args)

    def actuate(self, tool_name: str, tool_args: Any) -> ActuatorOutput:
        self.state.actuate()
        try:
            return self.actuator.actuate(tool_name=tool_name, tool_args=tool_args)
        finally:
            self.state.wait()

    def sense(self) -> SensoryOutput:
        self.state.sense()
        try:
            return self.sensor.sense()
        finally:
            self.state.wait()

    @classmethod
    def init(cls, task: str) -> "Autosphere":
        sphere = Autosphere(initial_task=task)
        sphere.setup()
        return sphere
