from autopack import Pack
from autopack.utils import run_args_from_args_schema

from beebot.body import Body
from beebot.body.pack_utils import llm_wrapper


class SystemBasePack(Pack):
    arbitrary_types_allowed = True

    body: Body

    def __init__(self, **kwargs):
        llm = llm_wrapper(kwargs.get("body"))

        run_args = {}
        if args_schema := kwargs.get("args_schema"):
            run_args = run_args_from_args_schema(args_schema)

        super().__init__(llm=llm, allm=llm, run_args=run_args, **kwargs)

    def _run(self, *args, **kwargs):
        raise NotImplementedError

    async def _arun(self, *args, **kwargs) -> str:
        return self._run(*args, **kwargs)
