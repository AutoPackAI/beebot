from pydantic import BaseModel

from beebot.packs.system_base_pack import SystemBasePack


class ExportVariableArgs(BaseModel):
    name: str
    value: str


class ExportVariable(SystemBasePack):
    name = "export_variable"
    description = (
        "Set and export a variable to make it globally available to other subtasks"
    )
    args_schema = ExportVariableArgs
    categories = []

    def _run(self, name: str, value: str) -> str:
        self.body.global_variables[name] = value
        return ""
