import logging
from typing import Callable, Type

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from beebot.body import Body
from beebot.packs.system_pack import SystemBasePack
from beebot.packs.utils import (
    get_module_path,
)

PACK_NAME = "exit"

logger = logging.getLogger(__name__)


class ExitArgs(BaseModel):
    success: bool = Field(..., description="Success")
    conclusion: str = Field(
        description="Summary of your experience on completing the task.", default=""
    )
    process_summary: str = Field(
        description="Summary of the task's efficiency.", default=""
    )
    function_summary: str = Field(
        description="Overview of function utilization and suggestions for improvements.",
        default="",
    )


def run_exit(
    body: Body,
    success: str,
    conclusion: str,
    process_summary: str,
    function_summary: str,
):
    body.state.finish()
    # TODO: Save the output somehow
    if success:
        logger.info("\n=== Task completed ===")
    else:
        logger.info("\n=== Task failed ===")

    logger.info(f"- Conclusion: {conclusion}")
    logger.info(f"- Process Summary: {process_summary}")
    logger.info(f"- Function Summary: {function_summary}")
    if body.config.hard_exit:
        exit()

    return "Exited"


PACK_DESCRIPTION = "Exits the program, signalling that all tasks have bene completed and all goals have been met."


class ExitTool(StructuredTool):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    func: Callable = run_exit
    args_schema: Type[BaseModel] = Type[ExitArgs]
    body: Body

    def _run(self, *args, **kwargs):
        return super()._run(*args, body=self.body, **kwargs)


class Exit(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = ExitTool
    args_schema: Type[BaseModel] = ExitArgs
