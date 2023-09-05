import logging
import os
from typing import ClassVar

import coloredlogs
from autopack.pack_config import PackConfig
from openai.util import logger as openai_logger
from pydantic import BaseSettings  # IDEAL_MODEL = "gpt-4-0613"
import openai

DEFAULT_DECOMPOSER_MODEL = "gpt-4"
FALLBACK_DECOMPOSER_MODEL = "gpt-3.5-turbo-16k-0613"
DEFAULT_PLANNER_MODEL = "gpt-3.5-turbo-16k-0613"
DEFAULT_DECIDER_MODEL = "gpt-3.5-turbo-16k-0613"
LOG_FORMAT = (
    "%(levelname)s %(asctime)s.%(msecs)03d %(filename)s:%(lineno)d- %(message)s"
)


class Config(BaseSettings):
    log_level: str = "INFO"

    openai_api_key: str = None
    helicone_key: str = None
    openai_api_base: str = None
    gmail_credentials_file: str = "credentials.json"
    decomposer_model: str = DEFAULT_DECOMPOSER_MODEL
    planner_model: str = DEFAULT_PLANNER_MODEL
    decider_model: str = DEFAULT_DECIDER_MODEL
    database_url: str = "sqlite://:memory:"

    workspace_path: str = "workspace"
    hard_exit: bool = False
    restrict_code_execution: bool = False
    process_timeout: int = 30
    pack_config: PackConfig = None

    _global_config: ClassVar["Config"] = None

    class Config:
        env_prefix = "beebot_"
        fields = {
            "database_url": {"env": "database_url"},
            "gmail_credentials_file": {"env": "gmail_credentials_file"},
            "helicone_key": {"env": "helicone_key"},
            "log_level": {"env": "log_level"},
            "openai_api_base": {"env": "openai_api_base"},
            "openai_api_key": {"env": "openai_api_key"},
        }

    def __init__(self, **kwargs) -> "Config":
        super().__init__(**kwargs)
        self.configure_autopack()
        self.setup_logging()
        self.configure_decomposer_model()

    def configure_decomposer_model(self):
        if self.decomposer_model == DEFAULT_DECOMPOSER_MODEL:
            model_ids = [model["id"] for model in openai.Model.list()["data"]]
            if self.decomposer_model not in model_ids:
                self.decomposer_model = FALLBACK_DECOMPOSER_MODEL

    def configure_autopack(self, is_global: bool = True):
        pack_config = PackConfig(
            workspace_path=self.workspace_path,
            restrict_code_execution=self.restrict_code_execution,
        )

        self.pack_config = pack_config

        if is_global:
            PackConfig.set_global_config(pack_config)

    def setup_logging(self) -> logging.Logger:
        os.makedirs("logs", exist_ok=True)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)

        file_handler = logging.FileHandler("logs/debug.log")
        file_handler.setLevel("DEBUG")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

        logging.basicConfig(
            level=self.log_level,
            format=LOG_FORMAT,
            datefmt="%H:%M:%S",
            handlers=[
                console_handler,
                file_handler,
            ],
        )

        coloredlogs.install(
            level=self.log_level,
            fmt=LOG_FORMAT,
            datefmt="%H:%M:%S",
        )

        # OpenAI will log a jsonified version of each request/response to `logger.debug` and we have our own logs
        # which are better formatted
        openai_logger.propagate = False

    @classmethod
    def set_global_config(cls, config_obj: "Config" = None) -> "Config":
        """
        Optionally set a global config object that can be used anywhere (You can still attach a separate instance to
        each Body)
        """
        cls._global_config = config_obj or cls()
        return cls._global_config

    @classmethod
    def global_config(cls) -> "Config":
        return cls._global_config or cls.set_global_config()
