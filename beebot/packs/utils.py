import json
import logging
import os
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any

from autopack.get_pack import try_get_pack
from autopack.installation import install_pack
from autopack.selection import select_packs
from pydantic import BaseModel

if TYPE_CHECKING:
    from autopack.pack import Pack
    from beebot.body import Body

logger = logging.getLogger(__name__)


def format_packs_to_openai_functions(packs: list["Pack"]) -> list[dict[str, Any]]:
    return [format_pack_to_openai_function(pack) for pack in packs]


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


def gather_packs(body: "Body", pack_limit: int = 3) -> list[str]:
    new_packs = suggested_packs(body=body, task=body.initial_task)

    initialized_packs = []
    for pack in new_packs:
        try:
            pack.init_tool(init_args=body.get_init_args(pack=pack))
            initialized_packs.append(pack)
        except Exception as e:
            logger.warning(f"Pack {pack.name} could not be initialized: {e}")

    body.packs += initialized_packs[:pack_limit]
    new_packs_list = ", ".join([pack.name for pack in initialized_packs[:pack_limit]])
    return new_packs_list


def suggested_packs(
    body: "Body", task: str, pack_limit: int = 3, cache: bool = True
) -> list["Pack"]:
    """This would be more convenient as an instance method on Body but good god is this long and unimportant to
    what the rest of it is doing. So it's here."""
    pack_ids = []
    cache_path = os.path.abspath(".autopack/selection_cache.json")

    # The initial task is the cache key, so we can't cache if we don't have it
    if not task:
        cache = False

    if cache:
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                cached_results = json.load(f)
            if body.initial_task in cached_results:
                pack_ids = cached_results.get(task)

    if not pack_ids:
        logger.info("Selecting packs")
        pack_ids = select_packs(task, body.brain.llm)[:pack_limit]
        logger.info(f"Packs selected: {pack_ids}")

    packs = get_packs_by_ids(body=body, pack_ids=pack_ids)
    used_pack_ids = [pack.pack_id for pack in packs]
    logger.info(f"Packs used: {used_pack_ids}")

    if cache:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w+") as f:
            try:
                existing_cache = json.load(f)
            except JSONDecodeError:
                existing_cache = {}

            existing_cache[body.initial_task] = used_pack_ids
            json.dump(existing_cache, f)

    return packs


def get_packs_by_ids(pack_ids: list[str], body: "Body") -> list["Pack"]:
    packs = []
    for pack_id in pack_ids:
        pack = try_get_pack(pack_id, quiet=False)

        if pack:
            packs.append(pack)
            continue

        if body.config.auto_install_packs:
            logger.info(f"Installing pack {pack_id}")
            try:
                pack = install_pack(
                    pack_id,
                    force_dependencies=body.config.auto_install_dependencies,
                )
            except Exception as e:
                logger.warning(f"Pack {pack_id} could not be loaded, skipping: {e}")
                continue

            if pack:
                packs.append(pack)
            else:
                logger.warning(f"Pack {pack_id} could not be installed")
                continue

        else:
            logger.warning(f"Pack {pack_id} is not installed")
            continue

    for pack in packs:
        try:
            init_args = body.get_init_args(pack=pack)
            pack.init_tool(init_args=init_args)
        except Exception as e:
            logger.warning(f"Pack {pack.pack_id} could not be loaded, skipping {e}")
            continue

    return packs
