import sys

from dotenv import load_dotenv

from beebot.autosphere import Autosphere


def run_specific_agent(task: str) -> None:
    load_dotenv()
    sphere = Autosphere.init(task)
    while output := sphere.cycle():
        print(output)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <task>")
        sys.exit(1)
    task = sys.argv[-1]
    run_specific_agent(task)
