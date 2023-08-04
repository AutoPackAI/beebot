from dataclasses import dataclass
from typing import TYPE_CHECKING

from beebot.models.database_models import (
    StepModel,
    Plan,
    Decision,
    Observation,
    Oversight,
    DocumentModel,
    DocumentStep,
)

if TYPE_CHECKING:
    from beebot.execution.execution_path import ExecutionPath


@dataclass
class Step:
    execution_path: "ExecutionPath" = None
    model_object: StepModel = None
    oversight: Oversight = None
    decision: Decision = None
    observation: Observation = None
    plan: Plan = None
    reversible: bool = True

    @property
    async def documents(self) -> dict[str, DocumentModel]:
        documents = {}
        if not self.model_object:
            return documents

        document_steps = await DocumentStep.filter(
            step=self.model_object
        ).prefetch_related("document")
        for document_step in document_steps:
            documents[document_step.document.name] = document_step.document

        return documents

    async def add_document(self, document: DocumentModel):
        await DocumentStep.get_or_create(document=document, step=self.model_object)

    async def save(self):
        if not self.model_object:
            self.model_object = StepModel(
                execution_path=self.execution_path.model_object,
                oversight=self.oversight,
                decision=self.decision,
                observation=self.observation,
                plan=self.plan,
            )
        else:
            self.model_object.oversight = self.oversight
            self.model_object.decision = self.decision
            self.model_object.observation = self.observation
            self.model_object.plan = self.plan

        await self.model_object.save()

    @classmethod
    async def from_model(cls, step_model: StepModel):
        kwargs = {"model_object": step_model, "reversible": False}
        oversight = await step_model.oversight
        decision = await step_model.decision
        observation = await step_model.observation
        plan = await step_model.plan

        if oversight:
            kwargs["oversight"] = oversight
        if decision:
            kwargs["decision"] = decision
        if observation:
            kwargs["observation"] = observation
        if plan:
            kwargs["plan"] = plan

        step = cls(**kwargs)

        return step
