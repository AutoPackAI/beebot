import subprocess
from typing import Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from beebot.body import Body


class BackgroundProcess:
    cmd: list[str]
    process: Optional[subprocess.Popen[str]] = None
    daemonize: bool = False

    def __init__(
        self,
        body: "Body",
        cmd: list[str],
        daemonize: bool = False,
    ):
        self.body = body
        self.cmd = cmd
        self.daemonize = daemonize
        self.process = None

    def run(self):
        process = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=self.body.config.workspace_path,
            start_new_session=self.daemonize,
        )

        self.body.processes[process.pid] = self
        self.process = process
        return process

    @property
    def pid(self) -> Union[int, None]:
        if self.process:
            return self.process.pid
        return None

    def poll(self):
        return self.process.poll()

    def communicate(self, *args, **kwargs) -> tuple[str, str]:
        return self.process.communicate(*args, **kwargs)

    def kill(self):
        return self.process.kill()

    @property
    def returncode(self) -> int:
        return self.process.returncode
