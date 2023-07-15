import logging
import os

from pydantic import BaseModel

# IDEAL_MODEL = "gpt-4-0613"
FALLBACK_MODEL = "gpt-3.5-turbo-16k-0613"
IDEAL_MODEL = FALLBACK_MODEL


class Config(BaseModel):
    openai_api_key: str = None
    helicone_key: str = None
    auto_install_packs: bool = True
    auto_install_dependencies: bool = True
    log_level: str = "INFO"
    hard_exit: bool = False
    workspace_path: str = "workspace"
    llm_model: str = IDEAL_MODEL
    gmail_credentials_file: str = "credentials.json"

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
        if (credentials_file := os.getenv("DEFAULT_CLIENT_SECRETS_FILE")) is not None:
            kwargs["gmail_credentials_file"] = credentials_file

        config = cls(**kwargs)
        config.setup_logging()
        return config

    def setup_logging(self) -> logging.Logger:
        os.makedirs("logs", exist_ok=True)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(logging.Formatter("%(message)s"))

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
