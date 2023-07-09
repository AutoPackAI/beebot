import logging
import os

from pydantic import BaseModel


class Config(BaseModel):
    openai_api_key: str = None
    auto_install_packs: bool = True
    auto_install_dependencies: bool = True
    log_level: str = "INFO"
    hard_exit: bool = False
    workspace_path: str = "workspace"

    @classmethod
    def from_env(cls) -> "Config":
        kwargs = {}

        # Go through and only supply kwargs if the values are actually set, otherwise Pydantic complains
        if (hard_exit := os.getenv("HARD_EXIT")) is not None:
            kwargs["hard_exit"] = hard_exit
        if (hard_exit := os.getenv("OPENAI_API_KEY")) is not None:
            kwargs["openai_api_key"] = hard_exit
        if (hard_exit := os.getenv("AUTO_INSTALL_PACKS")) is not None:
            kwargs["auto_install_packs"] = hard_exit
        if (hard_exit := os.getenv("AUTO_INSTALL_DEPENDENCIES")) is not None:
            kwargs["auto_install_dependencies"] = hard_exit
        if (hard_exit := os.getenv("LOG_LEVEL")) is not None:
            kwargs["log_level"] = hard_exit
        if (workspace_path := os.getenv("WORKSPACE_PATH")) is not None:
            kwargs["workspace_path"] = os.path.abspath(workspace_path)

        return cls(**kwargs)

    def custom_logger(self, name: str) -> logging.Logger:
        log = logging.getLogger(name)

        log.addHandler(logging.StreamHandler())
        log.setLevel(self.log_level)

        log.warning("Logging is set up")
        return log

    # A way to merge
    # Config from database
