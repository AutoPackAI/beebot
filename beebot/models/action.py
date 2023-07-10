from pydantic import Field, BaseModel


class Action(BaseModel):
    reasoning: str = Field()
    tool_name: str = Field(...)
    tool_args: dict = Field(default_factory=dict)

    def compressed_dict(self):
        """Return this output as a dict that is smaller so that it uses fewer tokens"""
        return {"tool": self.tool_name, "args": self.tool_args}
