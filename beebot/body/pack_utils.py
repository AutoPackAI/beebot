import logging
import subprocess
from typing import TYPE_CHECKING

from autopack.pack import Pack

from beebot.body.llm import call_llm

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)

# TODO: This should be a config value?
SUPPRESSED_PACKS = ["list_files", "delete_file"]


def llm_wrapper(body: "Body") -> str:
    async def llm(prompt) -> str:
        response = await call_llm(
            body, prompt, include_functions=False, function_call="none"
        )
        return response.text

    return llm


def init_workspace_poetry(workspace_path: str):
    """Make sure poetry is init'd in the workspace. The command errors if it is already init'd so just swallow the
    errors"""
    subprocess.run(
        ["poetry", "init", "--name", "beebot_workspace", "-n"],
        cwd=workspace_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def functions_detail_list(packs: list["Pack"]) -> str:
    pack_details = []
    for pack in packs:
        pack_args = []
        for arg_data in pack.args.values():
            arg_type = arg_data.get("type")
            if arg_type == "string":
                arg_type = "str"
            if arg_type == "boolean":
                arg_type = "bool"
            if arg_type == "number":
                arg_type = "int"
            pack_args.append(f"{arg_data.get('name')}: {arg_type}")

        pack_details.append(f"{pack.name}({', '.join(pack_args)})")

    return "\n".join(pack_details)
