import json
from typing import TYPE_CHECKING

from beebot.memory import Memory
from beebot.models import Plan, Observation
from beebot.models.database_models import MemoryChainModel, MemoryModel

if TYPE_CHECKING:
    from beebot.body import Body


class MemoryChain:
    """Generic memory storage model. Note that this is only internal memory of actions performed and should not be
    conflated with the concept of "memory" as defined in the vector memory space."""

    body: "Body"
    model_object: MemoryChainModel = None
    memories: list[Memory]
    uncompleted_memory: Memory

    def __init__(self, body: "Body", model_object: MemoryModel = None):
        self.body = body
        self.memories = []
        self.model_object = model_object
        self.uncompleted_memory = Memory()

    @classmethod
    def from_model(cls, body: "Body", chain_model: MemoryChainModel):
        chain = cls(body, model_object=chain_model)

        for memory_model in chain_model.memories:
            chain.memories.append(Memory.from_model(memory_model))

        return chain

    def add_plan(self, plan: Plan):
        self.uncompleted_memory.plan = plan

    def add_decision(self, decision: str):
        self.uncompleted_memory.decision = decision

    def add_observation(self, observation: Observation):
        self.uncompleted_memory.observation = observation

    def finish(self) -> Memory:
        completed_memory = self.uncompleted_memory

        # If the tool messed with memories (e.g. rewind) already we don't want to store it
        if self.uncompleted_memory.decision is None:
            self.uncompleted_memory = Memory()
            return self.uncompleted_memory

        self.uncompleted_memory = Memory()
        self.memories.append(completed_memory)
        self.persist_memory()
        return completed_memory

    def persist_memory(self):
        if not self.body.config.persistence_enabled:
            return

        if not self.model_object:
            chain_model = MemoryChainModel(body=self.body.model_object)
            chain_model.save()
            self.model_object = chain_model

        for memory in self.memories:
            if not memory.model_object:
                memory_model = MemoryModel(
                    memory_chain=self.model_object,
                    plan=memory.plan.persisted_dict,
                    decision=memory.decision.persisted_dict,
                    observation=memory.observation.persisted_dict,
                )
                memory_model.save()
                memory.model_object = memory_model

    def compile_history(self) -> str:
        if not self.memories:
            return ""

        memories_to_compile = list(self.memories)
        memory_table = []
        memory_outputs = {}

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
            formatted_outcome = (
                f"{i + 1}. You executed the function `{memory.decision.tool_name}` with the arguments "
                f"{json.dumps(memory.decision.tool_args)}: {outcome}."
            )
            if first_outcome_step := memory_outputs.get(formatted_outcome):
                formatted_outcome = (
                    f"{i + 1}. You executed the function `{memory.decision.tool_name}` with the arguments "
                    f"{json.dumps(memory.decision.tool_args)} and the results were the same as #{first_outcome_step}."
                )
            else:
                memory_outputs[formatted_outcome] = i + 1

            memory_table.append(formatted_outcome)

        return "\n".join(memory_table)
