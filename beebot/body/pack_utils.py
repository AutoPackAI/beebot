import inspect
import logging
from typing import TYPE_CHECKING

from autopack.get_pack import get_all_installed_packs

from beebot.body.llm import call_llm

if TYPE_CHECKING:
    from autopack.pack import Pack
    from beebot.body import Body

logger = logging.getLogger(__name__)


def all_packs(body: "Body") -> dict[str, "Pack"]:
    from beebot.packs.system_base_pack import SystemBasePack
    from beebot import packs

    return_packs = {}
    for name, klass in inspect.getmembers(packs):
        if (
            inspect.isclass(klass)
            and hasattr(klass, "__bases__")
            and SystemBasePack in klass.__bases__
        ):
            pack = klass(body=body)
            return_packs[pack.name] = pack

    wrapper = llm_wrapper(body)
    for pack in get_all_installed_packs():
        return_packs[pack.name] = pack(llm=wrapper)

    return return_packs


def system_packs(body: "Body") -> dict[str, "Pack"]:
    from beebot.packs import Exit, GetMoreTools, WriteFile, RewindActions

    return {
        "exit": Exit(body=body),
        "get_more_tools": GetMoreTools(body=body),
        # "read_file": ReadFile(body=body),
        "rewind_actions": RewindActions(body=body),
        "write_file": WriteFile(body=body),
    }


def llm_wrapper(body: "Body") -> str:
    def llm(prompt) -> str:
        return call_llm(body, prompt).text

    return llm
