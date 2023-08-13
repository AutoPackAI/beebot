import logging
from typing import TYPE_CHECKING, Union

from autopack import Pack
from pydantic import ValidationError

from beebot.body.pack_utils import llm_wrapper
from beebot.decider import Decider
from beebot.execution import Step
from beebot.execution.executor import Executor
from beebot.execution.task_state_machine import TaskStateMachine
from beebot.models.database_models import (
    Plan,
    Observation,
    TaskExecutionModel,
    Oversight,
    Decision,
)
from beebot.overseer.overseer import Overseer
from beebot.planner import Planner

if TYPE_CHECKING:
    from beebot.body import Body
    from beebot.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

RETRY_LIMIT = 3


class TaskExecution:
    """Represents one "branch" of execution that beebot has made during execution of a task"""

    body: "Body"
    agent: "BaseAgent"
    model_object: TaskExecutionModel = None
    state: TaskStateMachine
    packs: dict[str, Pack] = None
    steps: list[Step]
    agent_name: str = ""
    instructions: str = ""
    inputs: list[str]
    outputs: list[str]
    complete: bool = False

    # NOTE! Map of value to list of names
    variables: dict[str, list[str]]

    def __init__(
        self,
        body: "Body",
        model_object: TaskExecutionModel = None,
        agent_name: str = "",
        instructions: str = "",
        inputs: list[str] = None,
        outputs: list[str] = None,
        complete: bool = False,
    ):
        self.state = TaskStateMachine(self)
        self.body = body
        self.steps = []
        self.model_object = model_object
        self.packs = {}
        self.variables = {}

        if model_object:
            self.agent_name = model_object.agent
            self.instructions = model_object.instructions
            self.inputs = model_object.inputs
            self.outputs = model_object.outputs
            self.complete = model_object.complete
        else:
            self.agent_name = agent_name
            self.instructions = instructions or ""
            self.inputs = inputs or []
            self.outputs = outputs or []
            self.complete = complete

        from beebot.agents.base_agent import BaseAgent

        agent_classes = [agent for agent in BaseAgent.__subclasses__()]
        self.agent = BaseAgent(self)
        for agent_class in agent_classes:
            if self.agent_name == agent_class.NAME:
                self.agent = agent_class(self)

    @property
    def current_step(self):
        return self.steps[-1] if self.steps else None

    @classmethod
    async def from_model(cls, body: "Body", task_execution_model: TaskExecutionModel):
        task = cls(body, model_object=task_execution_model)

        task.state.current_state = TaskStateMachine.states_map[
            task_execution_model.state
        ]

        for step_model in await task_execution_model.steps.all():
            task.steps.append(await Step.from_model(step_model))

        if task.current_step and task.current_step.plan:
            await task.create_new_step()

        await task.get_packs()
        return task

    async def create_new_step(self) -> Step:
        await self.save()

        old_step = self.current_step

        if old_step:
            plan = old_step.plan
            # Current step has not finished. TODO: Is this the right thing to do?
            if not plan:
                return old_step

            oversight = Oversight(
                original_plan_text=plan.plan_text, modified_plan_text=plan.plan_text
            )
            await oversight.save()

            new_incomplete_step = Step(task_execution=self, oversight=oversight)
        else:
            new_incomplete_step = Step(task_execution=self)

        await new_incomplete_step.save()
        self.steps.append(new_incomplete_step)
        await self.save()
        # Create links from previous documents to this execution

        if old_step:
            previous_documents = await old_step.documents
            for document in previous_documents.values():
                await new_incomplete_step.add_document(document)
        else:
            await self.create_initial_oversight()

        return new_incomplete_step

    async def cycle(self) -> Union[Step, None]:
        if self.complete:
            return None

        if not self.current_step:
            await self.create_new_step()

        if not self.state.current_state == TaskStateMachine.oversight:
            self.state.oversee()

        await self.get_packs()
        oversight = self.current_step.oversight

        self.state.decide()
        await self.save()

        decision = await self.decide(oversight)
        await self.execute(decision)

        return_step = self.current_step
        if not self.complete:
            new_plan = await self.plan()
            await self.add_plan(new_plan)
            await self.finish_step()

        await self.save()
        return return_step

    async def add_oversight(self, oversight: Oversight):
        self.current_step.oversight = oversight
        await self.current_step.save()

    async def add_decision(self, decision: str):
        self.current_step.decision = decision
        await self.current_step.save()

    async def add_observation(self, observation: Observation):
        step = self.current_step
        variable_name = f"{step.decision.tool_name}_{len(self.steps)}"
        if observation.response in self.variables:
            self.variables[observation.response].append(variable_name)
        else:
            self.variables[observation.response] = [variable_name]
        step.observation = observation
        await step.save()

    async def add_plan(self, plan: Plan):
        self.current_step.plan = plan
        await self.current_step.save()

    async def finish_step(self) -> Step:
        completed_step = self.current_step
        await self.create_new_step()
        return completed_step

    async def save(self):
        if not self.model_object:
            path_model = TaskExecutionModel(
                body=self.body.model_object,
                agent=self.agent_name,
                instructions=self.instructions,
                inputs=self.inputs,
                outputs=self.outputs,
                complete=self.complete,
            )
            await path_model.save()
            self.model_object = path_model

        for step in self.steps:
            await step.save()

    async def get_packs(self) -> list[Pack]:
        for pack_class in self.agent.PACKS:
            from beebot.packs.system_base_pack import SystemBasePack

            if pack_class in SystemBasePack.__subclasses__():
                pack = pack_class(body=self.body)
            else:
                llm = llm_wrapper(self.body)
                pack = pack_class(llm=llm, allm=llm)
            self.packs[pack.name] = pack
        return self.packs

    async def execute(self, decision: Decision, retry_count: int = 0) -> Observation:
        """Execute a Decision and keep track of state"""
        try:
            result = await Executor(self).execute(decision=decision)
            await self.add_observation(result)
            return result
        except ValidationError as e:
            # It's likely the AI just sent bad arguments, try again.
            logger.warning(
                f"Invalid arguments received: {e}. {decision.tool_name}({decision.tool_args}"
            )
            if retry_count >= RETRY_LIMIT:
                return
            return await self.execute(decision, retry_count + 1)
        finally:
            if not self.complete:
                self.state.plan()
            await self.save()

    async def decide(self, oversight: Oversight = None) -> Decision:
        """Execute an action and keep track of state"""
        try:
            decision = await Decider(self).decide_with_retry(oversight=oversight)
            await self.add_decision(decision)

            return decision
        finally:
            self.state.execute()
            await self.save()

    async def plan(self) -> Plan:
        """Take the current task and history and develop a plan"""
        try:
            plan = await Planner(self).plan()
            await self.add_plan(plan)
            return plan
        finally:
            if not self.complete:
                self.state.oversee()
            await self.save()

    async def create_initial_oversight(self) -> Oversight:
        oversight = await Overseer(self).initial_oversight()
        await self.add_oversight(oversight)
        return oversight

    async def compile_history(self) -> str:
        return await self.agent.compile_history()

    def compile_variables(self) -> str:
        return self.agent.compile_variables()
