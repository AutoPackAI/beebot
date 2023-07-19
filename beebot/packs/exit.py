import logging
from typing import Type

from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "exit"
PACK_DESCRIPTION = "Exits the program, signalling that all tasks have bene completed and all goals have been met."

logger = logging.getLogger(__name__)


class ExitArgs(BaseModel):
    success: bool = Field(..., description="Success")
    categorization: str = Field(
        description="Assign a broad category to this task, ensuring it's general enough to protect sensitive details yet specific enough to group similar tasks.",
        default="",
    )
    conclusion: str = Field(
        description="Reflect on the task execution process. Highlight any challenges faced and potential alternative strategies.",
        default="",
    )
    function_summary: str = Field(
        description="Create a concise review of the functions used, their effectiveness, and pinpoint potential areas for future development to optimize task execution.",
        default="",
    )


class Exit(SystemBasePack):
    class Meta:
        name: str = PACK_NAME

    name: str = Meta.name
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = ExitArgs
    categories: list[str] = ["System"]

    def _run(
        self,
        success: bool,
        categorization: str = "",
        conclusion: str = "",
        function_summary: str = "",
    ) -> str:
        self.body.state.finish()
        # TODO: Save the output somehow
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
