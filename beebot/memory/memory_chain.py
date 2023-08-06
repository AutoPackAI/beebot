import json
import logging
from typing import TYPE_CHECKING

from beebot.executor.observation import Observation
from beebot.memory import Memory
from beebot.models.database_models import MemoryChainModel, MemoryModel
from beebot.planner.plan import Plan

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


class MemoryChain:
    """Generic memory storage model. Note that this is only internal memory of actions performed and should not be
    conflated with the concept of "memory" as defined in the vector memory space."""

    body: "Body"
    model_object: MemoryChainModel = None
    memories: list[Memory]

    def __init__(self, body: "Body", model_object: MemoryModel = None):
        self.body = body
        self.memories = []
        self.model_object = model_object

    @classmethod
    async def from_model(cls, body: "Body", chain_model: MemoryChainModel):
        chain = cls(body, model_object=chain_model)

        for memory_model in await chain_model.memories.all():
            chain.memories.append(Memory.from_model(memory_model))

        if chain.memories[-1].plan:
            await chain.create_incomplete_memory()

        return chain

    async def create_incomplete_memory(self) -> Memory:
        await self.persist_memory_chain()
        new_incomplete_memory = Memory(memory_chain=self)
        await new_incomplete_memory.persist_memory()

        # Create links from previous documents to this memory
        if len(self.memories):
            previous_documents = await self.memories[-1].documents
            for document in previous_documents.values():
                await new_incomplete_memory.add_document(document)

        self.memories.append(new_incomplete_memory)
        return new_incomplete_memory

    async def add_plan(self, plan: Plan):
        self.memories[-1].plan = plan
        await self.memories[-1].persist_memory()

    async def add_decision(self, decision: str):
        self.memories[-1].decision = decision
        await self.memories[-1].persist_memory()

    async def add_observation(self, observation: Observation):
        self.memories[-1].observation = observation
        await self.memories[-1].persist_memory()

    async def finish(self) -> Memory:
        completed_memory = self.memories[-1]

        await self.create_incomplete_memory()
        await self.persist_memory_chain()

        return completed_memory

    async def persist_memory_chain(self):
        if not self.model_object:
            chain_model = MemoryChainModel(body=self.body.model_object)
            await chain_model.save()
            self.model_object = chain_model

        for memory in self.memories:
            await memory.persist_memory()

    async def compile_history(self) -> str:
        if not self.memories:
            return ""

        memories_to_compile = list(self.memories)
        memory_table = []
        memory_outputs = {}

        # If the first memory is to rewind it meant that we started over, add some text to indicate that
        if (
            self.memories[0].decision
            and self.memories[0].decision.tool_name == "rewind_actions"
        ):
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

        # Compile the actual history
        for i, memory in enumerate(memories_to_compile):
            if not memory.observation:
                logger.debug(
                    f"Memory {memory.model_object.id} does not have observation, skipping"
                )
                continue

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

            # If this was a write_file immediately append a read_file afterwards so that unnecessary verification isn't
            # performed
            if memory.decision.tool_name == "write_file":
                name = memory.decision.tool_args.get("filename")
                content = memory.decision.tool_args.get("text_content")
                memory_table.append(history_item(len(memory_table) + 1, name, content))

        return "\n".join(memory_table)


def history_item(number: int, name: str, content: dict):
    return (
        f'{number}. You executed the function `read_file` with the arguments {{"filename": "{name}"}}: '
        f"{json.dumps(content)}."
    )
