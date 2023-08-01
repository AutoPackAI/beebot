from pydantic import Field, BaseModel


class Decision(BaseModel):
    tool_name: str = Field(...)
    tool_args: dict = Field(default_factory=dict)
    prompt_variables: dict[str, str] = Field(default_factory=dict)
    response: str = ""
