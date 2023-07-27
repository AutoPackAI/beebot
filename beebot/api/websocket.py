import asyncio
import json
import logging
from json import JSONDecodeError
from typing import Any

import psycopg2
from psycopg2._psycopg import connection
from starlette.websockets import WebSocket

from beebot.config import Config

logger = logging.getLogger(__name__)


async def producer(conn: connection) -> dict[str, dict[str, Any]]:
    while True:
        conn.poll()
        if conn.notifies:
            notify = conn.notifies.pop(0)
            try:
                parsed_payload = json.loads(notify.payload)
                return {notify.channel: parsed_payload}
            except JSONDecodeError as e:
                logger.error(f"Invalid NOTIFY payload received {e}: {notify.payload}")

        await asyncio.sleep(0.1)


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    config = Config.global_config()
    conn = psycopg2.connect(config.database_url)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    curs = conn.cursor()
    curs.execute("LISTEN beebot_notifications;")
    await websocket.send_json({"ready": True})
    while True:
        try:
            await websocket.send_json({"poll": True})
            notify = await producer(conn)
            if not notify:
                # Connection closed
                break

            await websocket.send_json(notify)

        except Exception as e:
            logger.error(f"Unknown error occurred in websocket connection: {e}")
        await asyncio.sleep(0.1)
