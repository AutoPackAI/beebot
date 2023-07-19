import asyncio

from agent_protocol import (
    Agent,
    StepResult,
    StepHandler,
)
from dotenv import load_dotenv

from beebot.body import Body


async def task_handler(task_input) -> StepHandler:
    print(f"Created task: {task_input}")
    body = Body(initial_task=task_input)
    body.setup()

    async def step_handler(step_input):
        print(f"Executing step for task {task_input}")
        output = body.cycle()
        return StepResult(
            output=output,
        )

    return step_handler


def main():
    load_dotenv()
    asyncio.run(Agent.handle_task(task_handler).start())


if __name__ == "__main__":
    main()
