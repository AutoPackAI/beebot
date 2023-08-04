import logging

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from beebot.body import Body
from beebot.body.body_state_machine import BodyStateMachine
from beebot.execution import Step
from beebot.models.database_models import BodyModel, StepModel

logger = logging.getLogger(__name__)


async def body_response(body: Body) -> JSONResponse:
    artifacts = [
        {"name": document.name, "content": document.content}
        for document in await body.file_manager.all_documents()
    ]
    return JSONResponse(
        {
            "task_id": str(body.model_object.id),
            "input": body.initial_task,
            "artifacts": artifacts,
        }
    )


async def step_response(step: Step, body: Body) -> JSONResponse:
    artifacts = [
        {"name": document.name, "content": document.content}
        for document in await body.file_manager.all_documents()
    ]
    step_output = {
        "plan": step.plan.json(),
        "decision": step.decision.json(),
        "observation": step.observation.json(),
        "reversible": step.reversible,
    }
    return JSONResponse(
        {
            "step_id": str(step.model_object.id),
            "task_id": str(body.model_object.id),
            "output": step_output,
            "artifacts": artifacts,
            "is_last": body.state.current_state == BodyStateMachine.done,
        }
    )


async def create_agent_task(request: Request) -> JSONResponse:
    request_data = await request.json()
    body = Body(request_data.get("input"))
    await body.setup()

    return await body_response(body)


async def execute_agent_task_step(request: Request) -> JSONResponse:
    task_id = request.path_params.get("task_id")
    try:
        body_model = await BodyModel.get(id=int(task_id)).prefetch_related(
            BodyModel.INCLUSIVE_PREFETCH
        )
    except ValueError:
        logger.error(f"Body ID {task_id} is invalid")
        raise HTTPException(status_code=404, detail="Invalid Task ID")

    if not body_model:
        logger.error(f"Body with ID {task_id} not found")
        raise HTTPException(status_code=404, detail="Task not found")

    body = await Body.from_model(body_model)
    step = await body.cycle()
    if not step:
        raise HTTPException(status_code=400, detail="Task is complete")

    return await step_response(step, body)


async def agent_task_ids(request: Request) -> JSONResponse:
    bodies = await BodyModel.filter()
    return JSONResponse([str(body.id) for body in bodies])


async def get_agent_task(request: Request) -> JSONResponse:
    task_id = request.path_params.get("task_id")
    body_model = await BodyModel.get(id=int(task_id)).prefetch_related(
        BodyModel.INCLUSIVE_PREFETCH
    )

    if not body_model:
        raise HTTPException(status_code=400, detail="Task not found")

    return await body_response(await Body.from_model(body_model))


async def list_agent_task_steps(request: Request) -> JSONResponse:
    task_id = request.path_params.get("task_id")
    body_model = await BodyModel.get(id=int(task_id)).prefetch_related(
        BodyModel.INCLUSIVE_PREFETCH
    )
    body = await Body.from_model(body_model)

    if not body_model:
        raise HTTPException(status_code=400, detail="Task not found")

    step_ids = [
        m.id for m in await body.current_execution_path.model_object.steps.all()
    ]

    return JSONResponse(step_ids)


async def get_agent_task_step(request: Request) -> JSONResponse:
    task_id = request.path_params.get("task_id")
    body_model = await BodyModel.get(id=int(task_id)).prefetch_related(
        BodyModel.INCLUSIVE_PREFETCH
    )

    if not body_model:
        raise HTTPException(status_code=400, detail="Task not found")

    step_id = request.path_params.get("step_id")
    step_model = await StepModel.get(id=int(step_id))

    if not step_model:
        raise HTTPException(status_code=400, detail="Step not found")

    body = await Body.from_model(body_model)
    step = await Step.from_model(step_model)
    return await step_response(step, body)
