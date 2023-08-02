from pydantic import BaseModel, Field


class Plan(BaseModel):
    plan_text: str
    prompt_variables: dict[str, str] = Field(default_factory=dict)
    response: str = ""
