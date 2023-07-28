import inspect
import logging
from typing import TYPE_CHECKING, Union

from autopack.get_pack import get_all_installed_packs, get_all_pack_info
from autopack.installation import install_pack
from autopack.pack import Pack
from autopack.pack_response import PackResponse

from beebot.body.llm import call_llm

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


def all_packs(body: "Body") -> dict[str, Union[Pack, PackResponse]]:
    """Merge locally-installed and system packs into one list"""
    all_pack_data = {}
    local_packs = all_local_packs(body)
    remote_packs = get_all_pack_info()
    for pack in remote_packs:
        all_pack_data[pack.name] = pack

    for pack in local_packs.values():
        all_pack_data[pack.name] = pack

    return all_pack_data


def all_local_packs(body: "Body") -> dict[str, Pack]:
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


def system_packs(body: "Body") -> dict[str, Pack]:
    from beebot.packs import Exit, GetMoreTools, RewindActions

    return {
        "exit": Exit(body=body),
        "get_more_tools": GetMoreTools(body=body),
        "rewind_actions": RewindActions(body=body),
    }


def llm_wrapper(body: "Body") -> str:
    def llm(prompt) -> str:
        return call_llm(body, prompt).text

    return llm


def get_or_install_pack(body: "Body", pack_name) -> Pack:
    available_packs = {pack.name: pack for pack in get_all_pack_info()}
    installed_pack = all_local_packs(body).get(pack_name)

    if not installed_pack:
        pack_info = available_packs.get(pack_name)
        installed_pack = install_pack(pack_info.pack_id)(llm=body.llm)

    return installed_pack
