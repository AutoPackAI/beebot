import inspect
import logging
import os
from typing import TYPE_CHECKING, Any, Type

from pydantic import BaseModel

if TYPE_CHECKING:
    from autopack.pack import Pack
    from beebot.body import Body

logger = logging.getLogger(__name__)


def format_packs_to_openai_functions(packs: list["Pack"]) -> list[dict[str, Any]]:
    return [format_pack_to_openai_function(pack) for pack in packs.values()]


def format_pack_to_openai_function(pack: "Pack") -> dict[str, Any]:
    # Change this if/when other LLMs support functions
    required = []
    run_args = pack.run_args
    for arg_name, arg in run_args.items():
        arg_required = arg.pop("required", [])
        if arg_required:
            required.append(arg_name)
        run_args[arg_name] = arg

    return {
        "name": pack.name,
        "description": pack.description,
        "parameters": {"type": "object", "properties": run_args},
        "required": required,
    }


def run_args_from_args_schema(args_schema: BaseModel) -> dict[str, dict[str, str]]:
    run_args = {}
    if not args_schema:
        return run_args

    schema = args_schema.schema()
    if not schema:
        return run_args

    for param_name, param in schema.get("properties", []).items():
        run_args[param_name] = {
            "type": param.get("type", param.get("anyOf", "string")),
            "name": param_name,
            "description": param.get("description", ""),
            "required": param_name in schema.get("required"),
        }
    return run_args


def get_module_path(file: str) -> str:
    module_path = os.path.abspath(file)
    module_directory = os.path.dirname(module_path)

    return os.path.relpath(module_directory, start=os.getcwd()).replace(os.sep, ".")


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

    return return_packs


def system_packs(body: "Body") -> dict["Pack"]:
    instantiated_packs = {}
    for pack_class in system_pack_classes():
        pack = pack_class(body=body)
        pack.init_tool()
        instantiated_packs[pack.name] = pack

    return instantiated_packs


def system_pack_classes() -> list[Type["Pack"]]:
    from beebot.packs.exit import Exit
    from beebot.packs.get_more_tools import GetMoreTools

    return [Exit, GetMoreTools]


def pack_summaries(body: "Body") -> list[dict[str, Any]]:
    summaries = []
    for pack_name, pack in all_packs(body=body).items():
        if not hasattr(pack, "__fields__"):
            logger.warning(f"Pack {pack} is not a Pydantic model")
            continue

        pack_fields = pack.__fields__
        description = pack_fields.get("description").default
        run_args = pack_fields.get("run_args").default or {}
        summaries.append(
            {
                "name": pack_name,
                "description": description,
                "arguments": run_args,
            }
        )
    return summaries
