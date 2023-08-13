from typing import TYPE_CHECKING

from statemachine import StateMachine, State

if TYPE_CHECKING:
    from beebot.execution.task_execution import TaskExecution


class TaskStateMachine(StateMachine):
    waiting = State(initial=True)
    planning = State()
    oversight = State()
    deciding = State()
    executing = State()
    done = State(final=True)

    execute = deciding.to(executing)
    plan = executing.to(planning)
    oversee = planning.to(oversight) | waiting.to(oversight)
    decide = oversight.to(deciding)
    finish = executing.to(done)

    def __init__(self, task_execution: "TaskExecution"):
        self.task_execution = task_execution
        super().__init__()
