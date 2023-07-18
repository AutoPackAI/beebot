from beebot.models.database_models import MemoryModel
from beebot.models.decision import Decision
from beebot.models.observation import Observation
from beebot.models.plan import Plan


class Memory:
    model_object: MemoryModel = None
    plan: Plan = None
    decision: Decision = None
    observation: Observation = None
    reversible: bool = True
