from typing import Type, TYPE_CHECKING

from autopack.pack import Pack
from langchain.tools import StructuredTool
from pydantic import BaseModel

if TYPE_CHECKING:
    from beebot.body import Body


class SystemBasePack(Pack):
    repo = "beebot"
    author = "autopack"
    dependencies: list[str] = None
    source: str = "self"
    args_schema: BaseModel = None
    tool: StructuredTool = None
    body: "Body"
    run_args: dict[str, dict[str, str]] = None
    init_args: dict[str, dict[str, str]] = None

    def __init__(self, **kwargs):
        from beebot.packs.utils import run_args_from_args_schema

        super().__init__(**kwargs)
        self.run_args = run_args_from_args_schema(self.args_schema)
        self.init_args = {"body": {"name": "body", "type": "Body", "required": True}}

    def init_tool(self, *args, **kwargs):
        self.tool = self.tool_class(body=self.body)


def system_pack_classes() -> list[Type["Pack"]]:
    from beebot.packs.exit import Exit
    from beebot.packs.get_more_functions import GetMoreFunctions
    from beebot.packs.read_file import ReadFile
    from beebot.packs.delete_file import DeleteFile
    from beebot.packs.write_file import WriteFile

    return [Exit, GetMoreFunctions, WriteFile, ReadFile, DeleteFile]


def system_packs(body: "Body") -> list["Pack"]:
    instantiated_packs = []
    for pack_class in system_pack_classes():
        pack = pack_class(body=body)
        pack.init_tool()
        instantiated_packs.append(pack)

    return instantiated_packs


def silent_pack_names() -> list[str]:
    """These classes won't get written to history"""
    from beebot.packs.exit import Exit
    from beebot.packs.get_more_functions import GetMoreFunctions

    return [Exit.name, GetMoreFunctions.name]
