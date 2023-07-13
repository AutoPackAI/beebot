import logging
import os
from copy import copy

from pydantic import BaseModel


class Config(BaseModel):
    openai_api_key: str = None
    helicone_key: str = None
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
            kwargs["hard_exit"] = hard_exit in ["True", True, "t", "true"]
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
        if (helicone_key := os.getenv("HELICONE_KEY")) is not None:
            kwargs["helicone_key"] = helicone_key

        config = cls(**kwargs)
        config.setup_logging()
        return config

    def setup_logging(self) -> logging.Logger:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(
            ColoredFormatter("%(message)s")
            # ColoredFormatter("[%(levelname)s][%(funcName)s] %(message)s")
        )

        file_handler = logging.FileHandler("logs/debug.log")
        file_handler.setLevel("DEBUG")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        logging.basicConfig(
            level=self.log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                console_handler,
                file_handler,
            ],
        )


LOG_LEVEL_TO_COLOR = {
    "DEBUG": 32,  # green
    "INFO": 36,  # cyan
    "WARNING": 33,  # yellow
    "ERROR": 31,  # red
    "CRITICAL": 41,  # white on red bg
}

PREFIX = "\033["
SUFFIX = "\033[0m"


class ColoredFormatter(logging.Formatter):
    def __init__(self, pattern):
        logging.Formatter.__init__(self, pattern)

    def format(self, record):
        colored_record = copy(record)
        levelname = colored_record.levelname
        seq = LOG_LEVEL_TO_COLOR.get(levelname, 37)  # default white
        colored_levelname = ("{0}{1}m{2}{3}").format(PREFIX, seq, levelname, SUFFIX)
        colored_record.levelname = colored_levelname
        return logging.Formatter.format(self, colored_record)
