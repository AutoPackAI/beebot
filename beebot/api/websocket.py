import psycopg2
import select
from starlette.websockets import WebSocket

from beebot.config import Config


async def producer(conn):
    if select.select([conn], [], [], 5) == ([], [], []):
        return

    conn.poll()
    return conn.notifies.pop(0)


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    config = Config.from_env()
    conn = psycopg2.connect(config.database_url)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    curs = conn.cursor()
    curs.execute("LISTEN body_changes;")
    curs.execute("LISTEN memory_chain_changes;")
    curs.execute("LISTEN memory_changes;")
    await websocket.send_json({"ready": True})
    while True:
        notify = await producer(conn)
        if not notify:
            # Connection closed
            break
        await websocket.send_json({notify.channel: notify.payload})
