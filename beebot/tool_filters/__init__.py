from typing import TYPE_CHECKING

from beebot.models import Decision
from beebot.models.observation import Observation
from beebot.models.plan import Plan
from beebot.tool_filters.filter_long_documents import filter_long_documents

if TYPE_CHECKING:
    from beebot.body import Body

FILTERS = {}

GLOBAL_FILTERS = [filter_long_documents]


def filter_output(
    body: "Body", plan: Plan, decision: Decision, observation: Observation
) -> Observation:
    """If any function call needs to have its content changed to make it more readable for our LLM, do it here."""
    tool_name = decision.tool_name
    if filter_fn := FILTERS.get(tool_name):
        new_response = filter_fn(body, plan, decision, observation)
        if new_response:
            observation.response = new_response

    for filter_fn in GLOBAL_FILTERS:
        new_response = filter_fn(body, plan, decision, observation)
        if new_response:
            observation.response = new_response

    return observation
