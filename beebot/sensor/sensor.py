from langchain.chat_models.base import BaseChatModel


class Sensor:
    llm: BaseChatModel

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
