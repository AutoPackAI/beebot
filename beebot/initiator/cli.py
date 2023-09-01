#!/usr/bin/env python
import argparse
import asyncio

from dotenv import load_dotenv

from beebot.body import Body
from beebot.config import Config
from beebot.models.database_models import initialize_db


def parse_args():
    parser = argparse.ArgumentParser(description="BeeBot CLI tool")

    parser.add_argument(
        "-t",
        "--task",
        help="Run a specific task, wrapped in quotes",
    )

    return parser.parse_args()


async def main():
    load_dotenv()
    parsed_args = parse_args()
    if parsed_args.task:
        task = parsed_args.task
    else:
        print("What would you like me to do?")
        print("> ", end="")
        task = input()

    config = Config.global_config()
    config.setup_logging()
    await initialize_db(config.database_url)

    body = Body(task=task, config=config)
    await body.setup()
    while output := await body.cycle():
        if output.observation:
            print("\n=== Cycle Output ===")
            print(output.observation.response)


if __name__ == "__main__":
    asyncio.run(main())
