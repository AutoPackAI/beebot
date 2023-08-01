from dataclasses import dataclass
from typing import TYPE_CHECKING

from beebot.models.database_models import (
    MemoryModel,
    DocumentModel,
    DocumentMemoryModel,
)
from beebot.models.decision import Decision
from beebot.models.observation import Observation
from beebot.models.plan import Plan

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
    def documents(self) -> dict[str, DocumentModel]:
        documents = {}
        if not self.model_object:
            return documents

        for document_memory in self.model_object.document_memories:
            documents[document_memory.document.name] = document_memory.document

        return documents

    def add_document(self, document: DocumentModel):
        DocumentMemoryModel.get_or_create(document=document, memory=self.model_object)

    def persist_memory(self):
        if not self.model_object:
            memory_model = MemoryModel(
                memory_chain=self.memory_chain.model_object,
            )
            if self.plan:
                memory_model.plan = self.plan.__dict__
            if self.decision:
                memory_model.decision = self.decision.__dict__
            if self.observation:
                memory_model.observation = self.observation.__dict__

            memory_model.save()
            self.model_object = memory_model

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
