import logging
import selectors
import subprocess
from threading import Thread
from typing import Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from beebot.body import Body

logger = logging.getLogger(__name__)


class BackgroundProcess:
    cmd: list[str]
    process: Optional[subprocess.Popen[str]] = None
    daemonize: bool = False
    output_thread: Thread = None
    stdout: str = ""
    stderr: str = ""

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

        # Create a thread for reading output from process without blocking
        self.output_thread = Thread(target=self.stdout_reader)
        self.output_thread.start()
        return process

    @property
    def pid(self) -> Union[int, None]:
        if self.process:
            return self.process.pid
        return None

    def poll(self):
        return self.process.poll()

    def kill(self):
        self.process.kill()

    @property
    def returncode(self) -> int:
        return self.process.returncode

    def stdout_reader(self):
        def read_stdout(stream):
            self.stdout += "\n".join(stream.readlines())
            logger.info(f"STDOUT: {self.stdout}")

        def read_stderr(stream):
            self.stderr += "\n".join(stream.readlines())
            logger.info(f"STDERR: {self.stderr}")

        stdout_selector = selectors.DefaultSelector()
        stdout_selector.register(self.process.stdout, selectors.EVENT_READ, read_stdout)

        stderr_selector = selectors.DefaultSelector()
        stderr_selector.register(self.process.stderr, selectors.EVENT_READ, read_stderr)

        while self.process.poll() is None:
            for selector_events in [stdout_selector.select(), stderr_selector.select()]:
                for key, _ in selector_events:
                    callback = key.data
                    callback(key.fileobj)

    def stderr_reader(self, process):
        pass
