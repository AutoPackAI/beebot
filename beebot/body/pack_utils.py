import inspect
import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from autopack.pack import Pack
    from beebot.body import Body

logger = logging.getLogger(__name__)


def format_packs_to_openai_functions(packs: dict[str, "Pack"]) -> list[dict[str, Any]]:
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


def system_packs(body: "Body") -> dict[str, "Pack"]:
    from beebot.packs.exit import Exit
    from beebot.packs.get_more_tools import GetMoreTools
    from beebot.packs.read_file import ReadFile
    from beebot.packs.write_file import WriteFile

    return {
        "exit": Exit(body=body),
        "get_more_tools": GetMoreTools(body=body),
        "read_file": ReadFile(body=body),
        "write_file": WriteFile(body=body),
    }


def functions_bulleted_list(packs: list["Pack"]) -> str:
    functions_string = []
    grouped_packs = {}
    for pack in packs:
        for category in pack.categories:
            if category not in grouped_packs:
                grouped_packs[category] = []
            grouped_packs[category].append(pack)

    for category, category_packs in grouped_packs.items():
        functions_string.append(f"\n## {category}")
        sorted_by_name = sorted(category_packs, key=lambda p: p.name)
        for pack in sorted_by_name:
            args_signature = ", ".join(
                [
                    f"{arg.get('name')}: {arg.get('type')}"
                    for arg in pack.run_args.values()
                ]
            )
            args_descriptions = (
                "; ".join(
                    [
                        f"{arg.get('name')} ({arg.get('type')}): {arg.get('description')}"
                        for arg in pack.run_args.values()
                    ]
                )
                or "None."
            )
            functions_string.append(
                f"- {pack.name}({args_signature}): {pack.description} | Arguments: {args_descriptions}"
            )

    return "\n".join(functions_string)


def functions_summary(body: "Body"):
    return ", ".join([f"{name}" for name in body.packs.keys()])
