import json
import os
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, Type

from autopack.get_pack import try_get_pack
from autopack.installation import install_pack
from autopack.pack import Pack
from autopack.selection import select_packs
from langchain.tools import BaseTool
from pydantic import BaseModel

if TYPE_CHECKING:
    from beebot.autosphere import Autosphere


def gather_packs(sphere: "Autosphere", cache: bool = True) -> list[Pack]:
    return system_packs(sphere)


def system_pack_classes() -> list[Type[BaseTool]]:
    from beebot.packs.task_complete import TaskComplete
    from beebot.packs.get_more_functions import GetMoreFunctions

    return [TaskComplete, GetMoreFunctions]


def system_packs(sphere: "Autosphere") -> list[BaseTool]:
    instantiated_packs = []
    for pack_class in system_pack_classes():
        pack = pack_class(sphere=sphere)
        pack.init_tool()
        instantiated_packs.append(pack)

    return instantiated_packs


def suggested_packs(
    sphere: "Autosphere", task: str, initial_task: str = None, cache: bool = True
) -> list[Pack]:
    """This would be more convenient as an instance method on Autosphere but good god is this long and unimportant to
    what the rest of it is doing. So it's here."""
    pack_ids = []
    cache_path = os.path.abspath(".autopack/selection_cache.json")

    # The initial task is the cache key so we can't cache if we don't have it
    if not initial_task:
        cache = False

    if cache:
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                cached_results = json.load(f)
            if sphere.initial_task in cached_results:
                pack_ids = cached_results.get(initial_task)

    if not pack_ids:
        sphere.logger.info("Selecting packs")
        pack_ids = select_packs(task, sphere.llm)
        sphere.logger.info(f"Packs selected: {pack_ids}")

    packs = get_packs_by_ids(sphere=sphere, pack_ids=pack_ids)
    used_pack_ids = [pack.pack_id for pack in packs]
    sphere.logger.info(f"Packs used: {used_pack_ids}")

    if cache:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w+") as f:
            try:
                existing_cache = json.load(f)
            except JSONDecodeError:
                existing_cache = {}

            existing_cache[sphere.initial_task] = used_pack_ids
            json.dump(existing_cache, f)

    return packs


def get_packs_by_ids(pack_ids: list[str], sphere: "Autosphere") -> list[Pack]:
    packs = []
    for pack_id in pack_ids:
        pack = try_get_pack(pack_id, quiet=False)

        if pack:
            packs.append(pack)
            continue

        if sphere.config.auto_install_packs:
            sphere.logger.info(f"Installing pack {pack_id}")
            try:
                pack = install_pack(
                    pack_id,
                    force_dependencies=sphere.config.auto_install_dependencies,
                )
            except Exception as e:
                sphere.logger.warning(
                    f"Pack {pack_id} could not be loaded, skipping: {e}"
                )
                continue

            if pack:
                packs.append(pack)
            else:
                sphere.logger.warning(f"Pack {pack_id} could not be installed")
                continue

        else:
            sphere.logger.warning(f"Pack {pack_id} is not installed")
            continue

    for pack in packs:
        try:
            init_args = sphere.get_init_args(pack=pack)
            pack.init_tool(init_args=init_args)
        except Exception as e:
            sphere.logger.warning(f"Pack {pack_id} could not be loaded, skipping {e}")
            continue

    return packs


def format_packs_to_openai_functions(packs: list[Pack]) -> list[dict[str, Any]]:
    return [format_pack_to_openai_function(pack) for pack in packs]


def format_pack_to_openai_function(pack: Pack) -> dict[str, Any]:
    # Change this if/when other LLMs support functions
    required = []
    run_args = pack.run_args
    for arg_name, arg in run_args.items():
        arg_required = arg.pop("required", "")
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
    schema = args_schema.schema()
    for param_name, param in schema.get("properties", []).items():
        run_args[param_name] = {
            "type": param.get("type", param.get("anyOf", "string")),
            "name": param_name,
            "description": param.get("description", ""),
            "required": param_name in schema.get("required"),
        }
    return run_args


def system_pack_init_args() -> dict[str, dict[str, str]]:
    return {"sphere": {"name": "sphere", "type": "Autosphere", "required": True}}


def get_module_path(file: str) -> str:
    module_path = os.path.abspath(file)
    module_directory = os.path.dirname(module_path)

    return os.path.relpath(module_directory, start=os.getcwd()).replace(os.sep, ".")
