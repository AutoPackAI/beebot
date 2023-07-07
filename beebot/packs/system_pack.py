from typing import TYPE_CHECKING

from autopack.pack import Pack
from langchain.tools import StructuredTool
from pydantic import BaseModel

if TYPE_CHECKING:
    from beebot.autosphere import Autosphere


class SystemBasePack(Pack):
    repo = "beebot"
    author = "autopack"
    dependencies: list[str] = None
    source: str = "self"
    args_schema: BaseModel = None
    tool: StructuredTool = None
    sphere: "Autosphere" = None
    run_args: dict[str, dict[str, str]] = None
    init_args: dict[str, dict[str, str]] = None

    def __init__(self, **kwargs):
        from beebot.packs.utils import run_args_from_args_schema

        super().__init__(**kwargs)
        self.run_args = run_args_from_args_schema(self.args_schema)

    def init_tool(self, *args, **kwargs):
        self.tool = self.tool_class(sphere=self.sphere)
