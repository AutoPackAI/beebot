import json
from typing import List

from beebot.memory import Memory
from beebot.models import Plan, Observation


class MemoryStorage:
    """Generic memory storage model. This class will decide _where_ the memory is stored. But for now just in RAM"""

    memories: List[Memory]
    uncompleted_memory: Memory

    def __init__(self):
        self.memories = []
        self.uncompleted_memory = Memory()

    def add_plan(self, plan: Plan):
        self.uncompleted_memory.plan = plan

    def add_decision(self, decision: str):
        self.uncompleted_memory.decision = decision

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
        for memory in self.memories:
            action_format = f"{memory.decision.tool_name}({memory.decision.tool_args})"
            outcome = (
                json.dumps(memory.observation.response)
                if memory.observation.success
                else memory.observation.error_reason
            )
            memory_table.append(f"- {action_format} -> {outcome}")

        return "\n".join(memory_table)
