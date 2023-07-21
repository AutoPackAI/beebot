from dataclasses import dataclass

from beebot.models.database_models import MemoryModel
from beebot.models.decision import Decision
from beebot.models.observation import Observation
from beebot.models.plan import Plan


@dataclass
class Memory:
    model_object: MemoryModel = None
    plan: Plan = None
    decision: Decision = None
    observation: Observation = None
    reversible: bool = True

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
