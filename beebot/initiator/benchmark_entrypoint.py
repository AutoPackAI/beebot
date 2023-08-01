import sys

from dotenv import load_dotenv

from beebot.body import Body
from beebot.config import Config
from beebot.models.database_models import initialize_db


def run_specific_agent(task: str) -> None:
    load_dotenv()

    config = Config.global_config()
    config.setup_logging()
    initialize_db(config.database_url)

    body = Body(initial_task=task, config=config)
    body.setup()
    while output := body.cycle():
        print(output.observation.response)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <task>")
        sys.exit(1)
    task = sys.argv[-1]
    run_specific_agent(task)
