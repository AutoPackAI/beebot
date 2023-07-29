import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from beebot.api.routes import (
    create_agent_task,
    execute_agent_task_step,
    agent_task_ids,
    get_agent_task,
    list_agent_task_steps,
    get_agent_task_step,
)
from beebot.api.websocket import websocket_endpoint
from beebot.config import Config
from beebot.models.database_models import initialize_db

logger = logging.getLogger(__name__)

ORIGINS = [
    "http://localhost:3000",
]


def create_app() -> FastAPI:
    load_dotenv()
    os.environ["BEEBOT_HARD_EXIT"] = "False"
    config = Config.global_config()
    config.setup_logging()
    if not config.persistence_enabled:
        logger.error("The API Requires persistence to be enabled")
        exit()

    initialize_db(config.database_url)

    app = FastAPI(
        title="BeeBot Agent Communication Protocol",
        description="",
        version="v1",
    )
    app.add_websocket_route("/notifications", websocket_endpoint)
    app.add_route("/agent/tasks", create_agent_task, methods=["POST"])
    app.add_route(
        "/agent/tasks/{task_id}/steps", execute_agent_task_step, methods=["POST"]
    )
    app.add_route("/agent/tasks", agent_task_ids)
    app.add_route("/agent/tasks/{task_id}", get_agent_task)
    app.add_route("/agent/tasks/{task_id}/steps", list_agent_task_steps)
    app.add_route("/agent/tasks/{task_id}/steps/{step_id}", get_agent_task_step)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
