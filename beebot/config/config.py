import logging
import os


class Config:
    openai_api_key: str = None
    auto_install_packs: bool = True
    auto_install_dependencies: bool = True
    log_level: str = "INFO"

    def __init__(self, *args, **kwargs):
        if openai_api_key := kwargs.get("openai_api_key"):
            self.openai_api_key = openai_api_key

        if auto_install_packs := kwargs.get("auto_install_packs"):
            self.auto_install_packs = auto_install_packs

        if auto_install_dependencies := kwargs.get("auto_install_dependencies"):
            self.auto_install_dependencies = auto_install_dependencies

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            auto_install_packs=os.getenv("AUTO_INSTALL_PACKS"),
            auto_install_dependencies=os.getenv("AUTO_INSTALL_DEPENDENCIES")
        )

    def custom_logger(self, name: str) -> logging.Logger:
        log = logging.getLogger(name)

        log.addHandler(logging.StreamHandler())
        log.setLevel(self.log_level)

        log.warning("Logging is set up")
        return log

    # A way to merge
    # Config from database
