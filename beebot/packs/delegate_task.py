from typing import Type

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "delegate_task"
PACK_DESCRIPTION = (
    "Delegate a complex task to a subordinate agent and return the output."
)


class DelegateTaskArgs(BaseModel):
    task: str = Field(..., description="The task to be accomplished by the agent")


class DelegateTask(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = DelegateTaskArgs
    categories: list[str] = ["Delegation"]
    reversible = False

    def _run(self, task: str) -> str:
        from beebot.body import Body

        try:
            subagent = Body(task)
            subagent.setup()
            subagent_output = []
            while output := subagent.cycle():
                subagent_output.append(output.observation.response)

            return "\n".join(subagent_output)

        except Exception as e:
            return f"Error: {e}"
