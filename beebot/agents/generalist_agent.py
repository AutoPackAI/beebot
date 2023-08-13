from beebot.agents import BaseAgent
from beebot.packs import GetWebsiteTextContent, ExportVariable, Exit
from beebot.packs.disk_usage import DiskUsage
from beebot.packs.filesystem.read_file import ReadFile
from beebot.packs.filesystem.write_file import WriteFile
from beebot.packs.google_search import GoogleSearch
from beebot.packs.http_request.http_request import HttpRequest
from beebot.packs.os_info.os_info import OSInfo
from beebot.packs.wikipedia_summarize import WikipediaPack


class GeneralistAgent(BaseAgent):
    NAME = "Generalist Agent"
    PACKS = [
        WikipediaPack,
        GoogleSearch,
        GetWebsiteTextContent,
        OSInfo,
        DiskUsage,
        HttpRequest,
        WriteFile,
        ReadFile,
        Exit,
        ExportVariable,
    ]
    DESCRIPTION = ""
