from typing import List

from beebot.memory import Memory
from beebot.models import Stimulus, Observation


class MemoryStorage:
    """Generic memory storage model. This class will decide _where_ the memory is stored. But for now just in RAM"""

    memories: List[Memory]
    uncompleted_memory: Memory

    def __init__(self):
        self.memories = []
        self.uncompleted_memory = Memory()

    def add_stimulus(self, stimulus: Stimulus):
        self.uncompleted_memory.stimulus = stimulus

    def add_action(self, action: str):
        self.uncompleted_memory.action = action

    def add_observation(self, observation: Observation):
        self.uncompleted_memory.observation = observation

    def finish(self):
        # TODO: Store this in a db or whatever
        completed_memory = self.uncompleted_memory
        self.uncompleted_memory = Memory()
        self.memories.append(completed_memory)
        return completed_memory

    def compile_history(self) -> str:
        if not self.memories:
            return ""

        memory_table = []
        for i, memory in enumerate(self.memories):
            action_format = f"{memory.action.tool_name}({memory.action.tool_args}"
            # Does stimulus matter here? Probably not
            memory_table.append(
                f"{i + 1}. {action_format} -> {memory.observation.response}"
            )

        return "\n".join(memory_table)
