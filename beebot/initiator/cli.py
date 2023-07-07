#!/usr/bin/env python
import argparse

from dotenv import load_dotenv

from beebot.autosphere import Autosphere


def parse_args():
    parser = argparse.ArgumentParser(description="BeeBot CLI tool")

    parser.add_argument(
        "-t",
        "--task",
        help="Run a specific task, wrapped in quotes",
    )

    return parser.parse_args()


def main():
    load_dotenv()
    parsed_args = parse_args()
    if parsed_args.task:
        task = parsed_args.task
    else:
        print("What would you like me to do?")
        print("> ", end="")
        task = input()

    sphere = Autosphere.init(task)
    while output := sphere.cycle():
        print(output)


if __name__ == "__main__":
    main()
