from typing import Any

from pydantic import BaseModel, Field

from beebot.body import Body


class SystemBasePack(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    body: Body
    dependencies: list[str] = Field(default_factory=list)
    args_schema: BaseModel = None
    depends_on: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    run_args: dict[str, dict[str, str]] = None

    def __init__(self, **kwargs):
        from beebot.body.pack_utils import run_args_from_args_schema

        super().__init__(**kwargs)
        self.run_args = run_args_from_args_schema(self.args_schema)

    def run(self, tool_input: dict[str, Any]) -> Any:
        if hasattr(self, "_run"):
            return self._run(**tool_input)
        raise NotImplementedError
