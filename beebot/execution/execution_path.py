import json
import logging
from typing import TYPE_CHECKING

from beebot.execution import Step
from beebot.models.database_models import (
    Plan,
    Observation,
    ExecutionPathModel,
    Oversight,
)

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


class ExecutionPath:
    """Represents one "branch" of execution that beebot has made during execution of a task"""

    body: "Body"
    model_object: ExecutionPathModel = None
    steps: list[Step]

    def __init__(self, body: "Body", model_object: ExecutionPathModel = None):
        self.body = body
        self.steps = []
        self.model_object = model_object

    @property
    def current_step(self):
        return self.steps[-1] if self.steps else None

    @classmethod
    async def from_model(cls, body: "Body", execution_path_model: ExecutionPathModel):
        path = cls(body, model_object=execution_path_model)

        for step_model in await execution_path_model.steps.all():
            path.steps.append(await Step.from_model(step_model))

        if path.current_step and path.current_step.plan:
            await path.create_new_step()

        return path

    async def create_branch_from(self, step_index: int = 0) -> "ExecutionPath":
        """Create a new Path object that branches off at the given step index"""
        new_path = ExecutionPath(body=self.body)
        await new_path.save()

        for step in self.steps[0:step_index]:
            new_step = Step(
                execution_path=self,
                oversight=step.oversight,
                decision=step.decision,
                observation=step.observation,
                plan=step.plan,
                reversible=step.reversible,
            )
            await new_step.save()

            for document in step.documents:
                await new_step.add_document(document)

            new_path.steps.append(new_step)

        await new_path.save()
        return new_path

    async def create_new_step(self) -> Step:
        await self.save()

        if self.current_step:
            plan = self.current_step.plan
            # Current step has not finished. TODO: Is this the right thing to do?
            if not plan:
                return self.current_step

            oversight = Oversight(
                original_plan_text=plan.plan_text, modified_plan_text=plan.plan_text
            )
            await oversight.save()

            new_incomplete_step = Step(execution_path=self, oversight=oversight)
        else:
            new_incomplete_step = Step(execution_path=self)

        await new_incomplete_step.save()

        # Create links from previous documents to this execution
        if self.current_step:
            previous_documents = await self.current_step.documents
            for document in previous_documents.values():
                await new_incomplete_step.add_document(document)

        self.steps.append(new_incomplete_step)
        await self.save()
        return new_incomplete_step

    async def add_oversight(self, oversight: Oversight):
        self.current_step.oversight = oversight
        await self.current_step.save()

    async def add_decision(self, decision: str):
        self.current_step.decision = decision
        await self.current_step.save()

    async def add_observation(self, observation: Observation):
        self.current_step.observation = observation
        await self.current_step.save()

    async def add_plan(self, plan: Plan):
        self.current_step.plan = plan
        await self.current_step.save()

    async def finish(self) -> Step:
        completed_step = self.current_step
        await self.create_new_step()
        return completed_step

    async def save(self):
        if not self.model_object:
            path_model = ExecutionPathModel(body=self.body.model_object)
            await path_model.save()
            self.model_object = path_model

        for step in self.steps:
            await step.save()

    async def compile_history(self) -> str:
        if not self.steps:
            return ""

        steps_to_compile = list(self.steps)
        step_table = []
        step_outputs = {}

        # If the first execution is to rewind it meant that we started over, add some text to indicate that
        first_memory = self.steps[0]
        if (
            first_memory
            and first_memory.decision
            and first_memory.decision.tool_name == "rewind_actions"
        ):
            if len(self.steps) == 1:
                step_table.append(
                    "The AI Assistant has attempted this task before, but it wasn't successful. Your actions have been "
                    "rewound and you will try an unconventional approach this time."
                )
            else:
                step_table.append(
                    "The AI Assistant had attempted this task before, and had rewound its actions. You had started "
                    "over and are trying an unconventional approach this time.\n"
                )

            # Don't include the rewind_action in the compiled history because we've already got this ^^
            steps_to_compile = steps_to_compile[1:]

        # Compile the actual history
        for i, step in enumerate(steps_to_compile):
            if not step.observation:
                continue

            outcome = (
                json.dumps(step.observation.response)
                if step.observation.success
                else step.observation.error_reason
            )
            formatted_outcome = (
                f"{len(step_table) + 1}. You executed the function `{step.decision.tool_name}` with the arguments "
                f"{json.dumps(step.decision.tool_args)}: {outcome}."
            )
            if first_outcome_step := step_outputs.get(formatted_outcome):
                formatted_outcome = (
                    f"{i + 1}. You executed the function `{step.decision.tool_name}` with the arguments "
                    f"{json.dumps(step.decision.tool_args)} and the results were the same as #{first_outcome_step}."
                )
            else:
                step_outputs[formatted_outcome] = i + 1

            step_table.append(formatted_outcome)

            # If this was a write_file immediately append a read_file afterwards so that unnecessary verification isn't
            # performed
            if step.decision.tool_name == "write_file":
                name = step.decision.tool_args.get("filename")
                content = step.decision.tool_args.get("text_content")
                step_table.append(history_item(len(step_table) + 1, name, content))

        return "\n".join(step_table)


def history_item(number: int, name: str, content: dict):
    return (
        f'{number}. You executed the function `read_file` with the arguments {{"filename": "{name}"}}: '
        f"{json.dumps(content)}."
    )
