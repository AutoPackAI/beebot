import os


class Config:
    openai_api_key: str = None

    def __init__(self, *args, **kwargs):
        self.openai_api_key = kwargs.get("openai_api_key")

    @classmethod
    def from_env(cls) -> "Config":
        openai_api_key = os.getenv("OPENAI_API_KEY")
        return cls(openai_api_key=openai_api_key)

    # A way to merge
    # Config from database
