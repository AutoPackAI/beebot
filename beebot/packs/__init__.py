from .analyze_webpage_content import AnalyzeWebpageContent
from .delegate_task import DelegateTask
from .disk_usage import DiskUsage
from .encyclopedia import Encyclopedia
from .execute_python_file import ExecutePythonFile
from .execute_python_file_in_background import ExecutePythonFileInBackground
from .exit import Exit
from .get_html_content import GetHtmlContent
from .get_more_tools import GetMoreTools
from .get_process_status import GetProcessStatus
from .gmail import CreateDraft, GetMessage, GetThread, Search, SendMessage
from .google_search import GoogleSearch
from .http_request import HttpRequest
from .install_python_package import InstallPythonPackage
from .kill_process import KillProcess
from .list_processes import ListProcesses
from .os_info import OSInfo
from .read_file import ReadFile
from .rewind_actions import RewindActions
from .wikipedia import Wikipedia
from .wolfram_alpha import WolframAlpha
from .write_file import WriteFile
from .write_python_file import WritePythonFile

__all__ = [
    "AnalyzeWebpageContent",
    "CreateDraft",
    "DelegateTask",
    # Disabled because we can't trust the AI to delete files. It can clean up after itself, deleting its own work.
    # "DeleteFile",
    "DiskUsage",
    "Encyclopedia",
    # Disabled since I think we want to force execution using files
    # "ExecutePythonCode",
    "ExecutePythonFile",
    "ExecutePythonFileInBackground",
    "Exit",
    "GetHtmlContent",
    "GetMessage",
    "GetMoreTools",
    "GetProcessStatus",
    "GetThread",
    # Disabled because I don't think it's ever used correctly. It can use HttpRequest or AnalyzeWebpageContent
    # "GetWebsiteTextContent",
    "GoogleSearch",
    "HttpRequest",
    "InstallPythonPackage",
    "KillProcess",
    # Disabled because the file list is included in its entirety in the prompt and it doesn't know how to use it.
    # "ListFiles",
    "ListProcesses",
    "OSInfo",
    "ReadFile",
    "RewindActions",
    "Search",
    "SendMessage",
    "Wikipedia",
    "WolframAlpha",
    "WriteFile",
    "WritePythonFile",
]
