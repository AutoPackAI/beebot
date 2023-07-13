from typing import TYPE_CHECKING

from autopack.pack import Pack
from langchain.tools import StructuredTool
from pydantic import BaseModel

if TYPE_CHECKING:
    from beebot.body import Body


class SystemBasePack(Pack):
    args_schema: BaseModel = None
    tool: StructuredTool = None
    body: "Body"
    run_args: dict[str, dict[str, str]] = None

    def __init__(self, **kwargs):
        from beebot.body.pack_utils import run_args_from_args_schema

        super().__init__(
            init_args={},
            dependencies=[],
            source="self",
            repo="beebot",
            author="autopack",
            **kwargs
        )
        self.run_args = run_args_from_args_schema(self.args_schema)

    def init_tool(self, *args, **kwargs):
        self.tool = self.tool_class(body=self.body)
