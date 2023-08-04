from typing import TYPE_CHECKING

from statemachine import StateMachine, State

if TYPE_CHECKING:
    from beebot.body import Body


class BodyStateMachine(StateMachine):
    setup = State(initial=True)
    planning = State()
    oversight = State()
    deciding = State()
    executing = State()
    done = State(final=True)

    execute = deciding.to(executing)
    plan = executing.to(planning)
    oversee = planning.to(oversight) | setup.to(oversight)
    decide = oversight.to(deciding)
    finish = executing.to(done)

    def __init__(self, body: "Body"):
        self.body = body
        super().__init__()
