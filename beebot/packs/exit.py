import logging

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "exit"
PACK_DESCRIPTION = "Exits the program, signalling that all tasks have bene completed and all goals have been met."

logger = logging.getLogger(__name__)


class ExitArgs(BaseModel):
    success: bool = Field(description="Success", default=True)
    conclusion: str = Field(
        description="Reflect on the task execution process.", default=""
    )


class Exit(SystemBasePack):
    class Meta:
        name = PACK_NAME

    name = Meta.name
    description = PACK_DESCRIPTION
    args_schema = ExitArgs
    categories = ["System"]

    def _run(self, *args, **kwargs) -> str:
        raise NotImplementedError

    async def _arun(self, success: bool = True, conclusion: str = "") -> str:
        task_execution = self.body.current_task_execution
        task_execution.state.finish()
        task_execution.complete = True
        await task_execution.save()
        if success:
            logger.info("\n=== Task completed ===")
        else:
            logger.info("\n=== Task failed ===")

        logger.info(conclusion)

        return "Exited"
