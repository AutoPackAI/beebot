from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel

from beebot.actuator import Actuator
from beebot.config import Config
from beebot.prompting import refine_task_prompt
from beebot.sensor import Sensor


class Autosphere:
    initial_task: str
    task: str
    llm: BaseChatModel
    actuator: Actuator
    sensor: Sensor
    config: Config

    def __init__(self, initial_task: str):
        self.initial_task = initial_task

    def setup(self):
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k-0613")
        self.actuator = Actuator()
        self.sensor = Sensor(llm=self.llm)
        self.config = Config.from_env()
        self.refine_task()

    def refine_task(self):
        refine_prompt = refine_task_prompt()
        refined = self.llm([refine_prompt.format(task=self.initial_task)])
        self.task = refined.content

    @classmethod
    def init(cls, task: str) -> "Autosphere":
        sphere = Autosphere(initial_task=task)
        sphere.setup()
        return sphere
