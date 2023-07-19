import logging
import os

from pydantic import BaseModel

# IDEAL_MODEL = "gpt-4-0613"
FALLBACK_MODEL = "gpt-3.5-turbo-16k-0613"
IDEAL_MODEL = FALLBACK_MODEL

TRUEISH = [
    "True",
    True,
    "t",
    "true",
]


class Config(BaseModel):
    openai_api_key: str = None
    helicone_key: str = None
    openai_api_base: str = None
    auto_install_packs: bool = True
    auto_install_dependencies: bool = True
    log_level: str = "INFO"
    hard_exit: bool = False
    workspace_path: str = "workspace"
    llm_model: str = IDEAL_MODEL
    gmail_credentials_file: str = "credentials.json"
    restrict_code_execution: bool = False
    database_url: str = ""
    process_timeout: int = 30

    @classmethod
    def from_env(cls) -> "Config":
        kwargs = {}

        # Go through and only supply kwargs if the values are actually set, otherwise Pydantic complains
        if (hard_exit := os.getenv("HARD_EXIT")) is not None:
            kwargs["hard_exit"] = hard_exit in TRUEISH
        if (openai_api_key := os.getenv("OPENAI_API_KEY")) is not None:
            kwargs["openai_api_key"] = openai_api_key
        if (auto_install_packs := os.getenv("AUTO_INSTALL_PACKS")) is not None:
            kwargs["auto_install_packs"] = auto_install_packs in TRUEISH
        if (
            auto_install_dependencies := os.getenv("AUTO_INSTALL_DEPENDENCIES")
        ) is not None:
            kwargs["auto_install_dependencies"] = auto_install_dependencies in TRUEISH
        if (log_level := os.getenv("LOG_LEVEL")) is not None:
            kwargs["log_level"] = log_level
        if (workspace_path := os.getenv("WORKSPACE_PATH")) is not None:
            kwargs["workspace_path"] = os.path.abspath(workspace_path)
        if (helicone_key := os.getenv("HELICONE_KEY")) is not None:
            kwargs["helicone_key"] = helicone_key
        if (openai_api_base := os.getenv("OPENAI_API_BASE")) is not None:
            kwargs["openai_api_base"] = openai_api_base
        if (credentials_file := os.getenv("DEFAULT_CLIENT_SECRETS_FILE")) is not None:
            kwargs["gmail_credentials_file"] = credentials_file
        if (process_timeout := os.getenv("PROCESS_TIMEOUT")) is not None:
            kwargs["process_timeout"] = int(process_timeout)
        if (database_url := os.getenv("DATABASE_URL")) is not None:
            kwargs["database_url"] = database_url
        if (
            restrict_code_execution := os.getenv("RESTRICT_CODE_EXECUTION")
        ) is not None:
            kwargs["restrict_code_execution"] = restrict_code_execution in TRUEISH

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

    @property
    def persistence_enabled(self):
        return self.database_url != ""
