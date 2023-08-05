import logging

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from beebot.body import Body
from beebot.body.body_state_machine import BodyStateMachine
from beebot.memory import Memory
from beebot.models.database_models import BodyModel, MemoryModel

logger = logging.getLogger(__name__)


async def body_response(body: Body) -> JSONResponse:
    documents = await body.file_manager.all_documents()
    artifacts = [
        {"name": document.name, "content": document.content}
        for document in documents
    ]
    return JSONResponse(
        {
            "task_id": str(body.model_object.id),
            "input": body.initial_task,
            "artifacts": artifacts,
        }
    )


def memory_response(memory: Memory, body: Body) -> JSONResponse:
    artifacts = [
        {"name": document.name, "content": document.content}
        for document in body.file_manager.all_documents()
    ]
    memory_output = {
        "plan": memory.plan.__dict__,
        "decision": memory.decision.__dict__,
        "observation": memory.observation.__dict__,
        "reversible": memory.reversible,
    }
    return JSONResponse(
        {
            "step_id": str(memory.model_object.id),
            "task_id": str(body.model_object.id),
            "output": memory_output,
            "artifacts": artifacts,
            "is_last": body.state.current_state == BodyStateMachine.done,
        }
    )


async def create_agent_task(request: Request) -> JSONResponse:
    import pydevd_pycharm
    pydevd_pycharm.settrace('localhost', port=9739, stdoutToServer=True, stderrToServer=True)
    request_data = await request.json()
    body = Body(request_data.get("input"))
    await body.setup()

    return body_response(body)


async def execute_agent_task_step(request: Request) -> JSONResponse:
    task_id = request.path_params.get("task_id")
    try:
        body_model = await BodyModel.get(id=int(task_id)).prefetch_related(
            "memory_chains__memories__document_memories__document"
        )
    except ValueError:
        logger.error(f"Body ID {task_id} is invalid")
        raise HTTPException(status_code=404, detail="Invalid Task ID")

    if not body_model:
        logger.error(f"Body with ID {task_id} not found")
        raise HTTPException(status_code=404, detail="Task not found")

    body = await Body.from_model(body_model)
    memory = await body.cycle()
    if not memory:
        raise HTTPException(status_code=400, detail="Task is complete")

    return memory_response(memory, body)


async def agent_task_ids(request: Request) -> JSONResponse:
    bodies = await BodyModel.filter()
    return JSONResponse([str(body.id) for body in bodies])


async def get_agent_task(request: Request) -> JSONResponse:
    task_id = request.path_params.get("task_id")
    body_model = await BodyModel.get(id=int(task_id))

    if not body_model:
        raise HTTPException(status_code=400, detail="Task not found")

    return body_response(await Body.from_model(body_model))


async def list_agent_task_steps(request: Request) -> JSONResponse:
    task_id = request.path_params.get("task_id")
    body_model = await BodyModel.get(id=int(task_id))
    body = await Body.from_model(body_model)

    if not body_model:
        raise HTTPException(status_code=400, detail="Task not found")

    memory_ids = [
        m.model_object.id for m in body.current_memory_chain.current_memory_chain
    ]

    return JSONResponse(memory_ids)


async def get_agent_task_step(request: Request) -> JSONResponse:
    task_id = request.path_params.get("task_id")
    body_model = await BodyModel.get(id=int(task_id))

    if not body_model:
        raise HTTPException(status_code=400, detail="Task not found")

    step_id = request.path_params.get("step_id")
    memory_model = await MemoryModel.get(id=int(step_id))

    if not memory_model:
        raise HTTPException(status_code=400, detail="Step not found")

    body = await Body.from_model(body_model)
    memory = await Memory.from_model(memory_model)
    return memory_response(memory, body)
