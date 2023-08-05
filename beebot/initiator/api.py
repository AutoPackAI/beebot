import asyncio
import logging
import os
from fastapi import Depends

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

async def startup_event():
    load_dotenv()
    os.environ["BEEBOT_HARD_EXIT"] = "False"
    config = Config.global_config()
    config.setup_logging()
    await initialize_db(config.database_url)

app = FastAPI(
    title="BeeBot Agent Communication Protocol",
    description="",
    version="v1",
)

app.add_event_handler("startup", startup_event)
app.add_websocket_route("/notifications", websocket_endpoint)
app.add_route("/agent/tasks", create_agent_task, methods=["POST"])
