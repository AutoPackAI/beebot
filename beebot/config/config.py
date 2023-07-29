import logging
import os
from typing import ClassVar

import coloredlogs
from autopack.filesystem_emulation.filesystem_file_manager import FileSystemManager
from autopack.filesystem_emulation.ram_file_manager import RAMFileManager
from autopack.filesystem_emulation.workspace_file_manager import WorkspaceFileManager
from autopack.pack_config import PackConfig, InstallerStyle
from openai.util import logger as openai_logger
from pydantic import BaseSettings  # IDEAL_MODEL = "gpt-4-0613"

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
    database_url: str = ""

    workspace_path: str = "workspace"
    hard_exit: bool = False
    restrict_code_execution: bool = False
    process_timeout: int = 30
    auto_install_packs: bool = True
    auto_install_dependencies: bool = True
    file_manager: str = "workspace"
    auto_include_packs: list[str] = ["read_file", "write_file"]

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

    def configure_autopack(self):
        if self.auto_install_packs and self.auto_install_dependencies:
            installer_style = InstallerStyle.automatic
        elif self.auto_install_packs:
            installer_style = InstallerStyle.semiautomatic
        else:
            installer_style = InstallerStyle.manual

        if self.file_manager == "filesystem":
            file_manager_class = FileSystemManager
        elif self.file_manager == "ram":
            file_manager_class = RAMFileManager
        else:
            file_manager_class = WorkspaceFileManager

        pack_config = PackConfig(
            workspace_path=self.workspace_path,
            restrict_code_execution=self.restrict_code_execution,
            installer_style=installer_style,
        )
        pack_config.init_filesystem_manager(file_manager_class)

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

    @property
    def persistence_enabled(self):
        return self.database_url != ""

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
