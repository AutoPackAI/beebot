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
    incomplete_memory: Memory

    def __init__(self, body: "Body", model_object: MemoryModel = None):
        self.body = body
        self.memories = []
        self.model_object = model_object
        self.incomplete_memory = None
        self.create_incomplete_memory()

    @classmethod
    def from_model(cls, body: "Body", chain_model: MemoryChainModel):
        chain = cls(body, model_object=chain_model)

        for memory_model in chain_model.memories:
            chain.memories.append(Memory.from_model(memory_model))

        return chain

    def create_incomplete_memory(self) -> Memory:
        new_incomplete_memory = Memory(memory_chain=self)
        new_incomplete_memory.persist_memory()

        # Create links from previous documents to this memory
        if self.incomplete_memory:
            for document in self.incomplete_memory.documents.values():
                new_incomplete_memory.add_document(document)

        self.incomplete_memory = new_incomplete_memory
        return self.incomplete_memory

    def add_plan(self, plan: Plan):
        self.incomplete_memory.plan = plan
        self.incomplete_memory.persist_memory()

    def add_decision(self, decision: str):
        self.incomplete_memory.decision = decision
        self.incomplete_memory.persist_memory()

    def add_observation(self, observation: Observation):
        self.incomplete_memory.observation = observation
        self.incomplete_memory.persist_memory()

    def finish(self) -> Memory:
        completed_memory = self.incomplete_memory

        # If the tool messed with memories (e.g. rewind) already we don't want to store it
        # TODO: Maybe we do?
        if self.incomplete_memory.decision is None:
            self.create_incomplete_memory()
            return self.incomplete_memory

        self.create_incomplete_memory()
        self.memories.append(completed_memory)
        self.persist_memory_chain()
        return completed_memory

    def persist_memory_chain(self):
        if not self.model_object:
            chain_model = MemoryChainModel(body=self.body.model_object)
            chain_model.save()
            self.model_object = chain_model

        for memory in self.memories:
            memory.persist_memory()

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
                f"{len(memory_table) + 1}. You executed the function `{memory.decision.tool_name}` with the arguments "
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

        for file in self.body.file_manager.all_documents():
            memory_table.append(
                f"{len(memory_table) + 1}. You executed the function `read_file` with the arguments "
                f'{{"filename": "{file.name}"}}: {json.dumps(file.content)}.'
            )

        return "\n".join(memory_table)
