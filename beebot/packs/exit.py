import logging

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "exit"
PACK_DESCRIPTION = "Exits the program, signalling that all tasks have bene completed and all goals have been met."

logger = logging.getLogger(__name__)


class ExitArgs(BaseModel):
    success: bool = Field(..., description="Success")
    categorization: str = Field(
        description="Assign a broad category to this task, ensuring it's general enough to protect sensitive details "
        "yet specific enough to group similar tasks.",
        default="",
    )
    conclusion: str = Field(
        description="Reflect on the task execution process. Highlight any challenges faced and potential alternative "
        "strategies.",
        default="",
    )
    function_summary: str = Field(
        description="Create a concise review of each function that you used.",
        default="",
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

    async def _arun(
        self,
        success: bool,
        categorization: str = "",
        conclusion: str = "",
        function_summary: str = "",
    ) -> str:
        self.body.state.finish()
        await self.body.current_memory_chain.persist_memory_chain()
        if success:
            logger.info("\n=== Task completed ===")
        else:
            logger.info("\n=== Task failed ===")

        logger.info(f"- Categorization: {categorization}")
        logger.info(f"- Conclusion: {conclusion}")
        logger.info(f"- Function Summary: {function_summary}")

        for pid, process in self.body.processes.items():
            logger.info(f"\n=== Killing subprocess {pid} ===")
            process.kill()

        if self.body.config.hard_exit:
            exit()

        return "Exited"
