from typing import TYPE_CHECKING

from statemachine import StateMachine, State

if TYPE_CHECKING:
    from beebot.body import Body


class BodyStateMachine(StateMachine):
    setup = State(initial=True)
    starting = State()
    planning = State()
    deciding = State()
    executing = State()
    waiting = State()
    done = State(final=True)

    start = setup.to(starting)
    plan = starting.to(planning) | waiting.to(planning)
    decide = waiting.to(deciding)
    execute = waiting.to(executing)
    wait = (
        deciding.to(waiting)
        | planning.to(waiting)
        | executing.to(waiting)
        | starting.to(waiting)
    )
    finish = waiting.to(done) | executing.to(done)

    def __init__(self, body: "Body"):
        self.body = body
        super().__init__()

    def on_enter_state(self, event, state):
        """
        Whenever state changes persist the state change
        This is probably a bad place to put this logic.
        """
        if self.body.model_object:
            self.body.model_object.current_task = self.body.task
            self.body.model_object.state = state.value
            self.body.model_object.packs = self.body.packs.keys()
            self.body.model_object.save()
            self.body.file_manager.flush_to_directory(self.body.config.workspace_path)
