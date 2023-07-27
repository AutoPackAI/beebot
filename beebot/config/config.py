import logging
import os
from typing import ClassVar

import coloredlogs
from pydantic import BaseSettings

# IDEAL_MODEL = "gpt-4-0613"
FALLBACK_MODEL = "gpt-3.5-turbo-16k-0613"
IDEAL_MODEL = FALLBACK_MODEL
LOG_FORMAT = (
    "%(levelname)s %(asctime)s.%(msecs)03d %(filename)s:%(lineno)d- %(message)s"
)


class Config(BaseSettings):
    log_level: str = "INFO"

    openai_api_key: str = None
    helicone_key: str = None
    openai_api_base: str = None
    gmail_credentials_file: str = "credentials.json"
    llm_model: str = IDEAL_MODEL

    workspace_path: str = "workspace"
    hard_exit: bool = False
    database_url: str = ""
    restrict_code_execution: bool = False
    process_timeout: int = 30
    auto_install_packs: bool = True
    auto_install_dependencies: bool = True

    _global_config: ClassVar["Config"] = None

    class Config:
        env_prefix = "beebot_"
        fields = {
            "log_level": {
                "env": "log_level",
            },
            "openai_api_key": {"env": "openai_api_key"},
            "helicone_key": {"env": "helicone_key"},
            "openai_api_base": {"env": "openai_api_base"},
            "gmail_credentials_file": {"env": "gmail_credentials_file"},
        }

    def __init__(self, **kwargs) -> "Config":
        super().__init__(**kwargs)
        self.setup_logging()

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

    @property
    def persistence_enabled(self):
        return self.database_url != ""

    @classmethod
    def set_global_config(cls, config_obj: "PackConfig" = None) -> "PackConfig":
        """
        Optionally set a global config object that can be used anywhere (You can still attach a separate instance to
        each Body)
        """
        cls._global_config = config_obj or cls()
        return cls._global_config

    @classmethod
    def global_config(cls) -> "PackConfig":
        return cls._global_config or cls.set_global_config()
