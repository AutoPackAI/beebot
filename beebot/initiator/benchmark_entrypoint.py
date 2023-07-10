import sys

from dotenv import load_dotenv

from beebot.body import Body


def run_specific_agent(task: str) -> None:
    load_dotenv()
    body = Body(task)
    body.setup()
    while output := body.cycle():
        print(output)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <task>")
        sys.exit(1)
    task = sys.argv[-1]
    run_specific_agent(task)
