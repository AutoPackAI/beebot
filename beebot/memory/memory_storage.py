import json

from beebot.memory import Memory
from beebot.models import Plan, Observation


class MemoryStorage:
    """Generic memory storage model. This class will decide _where_ the memory is stored. But for now just in RAM"""

    memories: list[Memory]
    old_memories: list[list[Memory]]
    uncompleted_memory: Memory

    def __init__(self):
        self.memories = []
        self.old_memories = []
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

        memories_to_compile = list(self.memories)
        memory_table = []

        # If the first memory is to rewind it meant that we started over, add some text to indicate that
        if self.memories[0].decision.tool_name == "rewind_actions":
            if len(self.memories) == 1:
                memory_table.append(
                    "The AI Assistant has attempted this task before, but it wasn't successful. Your actions have been "
                    "rewound and you will try an unconventional approach this time."
                )
            else:
                memory_table.append(
                    "The AI Assistant had attempted this task before, and had rewound its actions. You had started "
                    "over and are trying an unconventional approach this time.\n"
                )

            # Don't include the rewind_action in the compiled history because we've already got this ^^
            memories_to_compile = memories_to_compile[1:]

        for i, memory in enumerate(memories_to_compile):
            outcome = (
                json.dumps(memory.observation.response)
                if memory.observation.success
                else memory.observation.error_reason
            )
            memory_table.append(
                f"{i + 1}. You executed the function `{memory.decision.tool_name}` with the arguments "
                f"{json.dumps(memory.decision.tool_args)}. The result was {outcome}."
            )

        return "\n".join(memory_table)
