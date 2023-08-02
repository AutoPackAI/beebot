import subprocess
import sys


def run_specific_agent(task: str) -> None:
    command = [
        "poetry",
        "run",
        "python",
        "-m",
        "beebot.initiator.benchmark_entrypoint",
        task,
    ]
    subprocess.run(command, text=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <task>")
        sys.exit(1)
    task = sys.argv[-1]
    run_specific_agent(task)
