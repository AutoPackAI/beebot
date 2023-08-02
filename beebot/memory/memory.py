from dataclasses import dataclass
from typing import TYPE_CHECKING

from beebot.decider.decision import Decision
from beebot.executor.observation import Observation
from beebot.models.database_models import (
    MemoryModel,
    DocumentModel,
    DocumentMemoryModel,
)
from beebot.planner.plan import Plan

if TYPE_CHECKING:
    from beebot.memory.memory_chain import MemoryChain


@dataclass
class Memory:
    memory_chain: "MemoryChain" = None
    model_object: MemoryModel = None
    plan: Plan = None
    decision: Decision = None
    observation: Observation = None
    reversible: bool = True

    @property
    async def documents(self) -> dict[str, DocumentModel]:
        documents = {}
        if not self.model_object:
            return documents

        document_memories = await DocumentMemoryModel.filter(
            memory=self.model_object
        ).prefetch_related("document")
        for document_memory in document_memories:
            documents[document_memory.document.name] = document_memory.document

        return documents

    async def add_document(self, document: DocumentModel):
        await DocumentMemoryModel.get_or_create(
            document=document, memory=self.model_object
        )

    async def persist_memory(self):
        if not self.model_object:
            self.model_object = MemoryModel(
                memory_chain=self.memory_chain.model_object,
            )

        if self.plan:
            self.model_object.plan = self.plan.__dict__
        if self.decision:
            self.model_object.decision = self.decision.__dict__
        if self.observation:
            self.model_object.observation = self.observation.__dict__

        await self.model_object.save()

    @classmethod
    def from_model(cls, memory_model: MemoryModel):
        plan = Plan(**memory_model.plan)
        decision = Decision(**memory_model.decision)
        observation = Observation(**memory_model.observation)
        memory = cls(
            model_object=memory_model,
            reversible=False,
            plan=plan,
            decision=decision,
            observation=observation,
        )

        return memory
