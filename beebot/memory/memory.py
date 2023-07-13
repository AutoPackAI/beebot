from beebot.models.decision import Decision
from beebot.models.observation import Observation
from beebot.models.plan import Plan


class Memory:
    plan: Plan = None
    decision: Decision = None
    observation: Observation = None
