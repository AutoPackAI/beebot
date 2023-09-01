import asyncio
import sys

from dotenv import load_dotenv

from beebot.body import Body
from beebot.config import Config
from beebot.models.database_models import initialize_db


async def run_specific_agent(task: str) -> None:
    load_dotenv()

    config = Config.global_config()
    config.setup_logging()
    await initialize_db(config.database_url)

    body = Body(task=task, config=config)
    await body.setup()
    while output := await body.cycle():
        if output.observation:
            print(output.observation.response)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <task>")
        sys.exit(1)
    task_arg = sys.argv[-1]
    asyncio.run(run_specific_agent(task_arg))
