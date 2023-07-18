from pydantic import Field, BaseModel


class Decision(BaseModel):
    tool_name: str = Field(...)
    tool_args: dict = Field(default_factory=dict)

    @property
    def persisted_dict(self):
        return self.__dict__
