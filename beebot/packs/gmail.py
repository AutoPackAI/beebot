from langchain.tools.gmail.create_draft import GmailCreateDraft as CreateDraftTool
from langchain.tools.gmail.get_message import GmailGetMessage as GetMessageTool
from langchain.tools.gmail.get_thread import GmailGetThread as GetThreadTool
from langchain.tools.gmail.search import GmailSearch as SearchTool
from langchain.tools.gmail.send_message import GmailSendMessage as SendMessageTool

from beebot.body.pack_utils import get_module_path
from beebot.packs.system_base_pack import SystemBasePack

tools = [CreateDraftTool, GetMessageTool, GetThreadTool, SearchTool, SendMessageTool]


class CreateDraft(SystemBasePack):
    class Meta:
        name: str = "gmail_create_draft"

    name: str = Meta.name
    description: str = CreateDraftTool.description
    pack_id: str = f"autopack/beebot/{PACK_NAME}"
    module_path = get_module_path(__file__)
    tool_class: Type = CreateDraftTool
    args_schema: Type[BaseModel] = GetPacksArgs
