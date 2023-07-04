#!/usr/bin/env python
from dotenv import load_dotenv

from beebot.autosphere import Autosphere


def main():
    load_dotenv()
    print("What would you like me to do?")
    print("> ", end="")
    task = input()
    Autosphere.init(task)


if __name__ == "__main__":
    main()
