from beebot.models.action import Action
from beebot.models.observation import Observation
from beebot.models.stimulus import Stimulus


class Memory:
    stimulus: Stimulus = None
    action: Action = None
    observation: Observation = None
