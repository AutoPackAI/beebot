from langchain.tools.gmail.create_draft import (
    GmailCreateDraft as CreateDraftTool,
)
from langchain.tools.gmail.get_message import (
    GmailGetMessage as GetMessageTool,
    SearchArgsSchema,
)
from langchain.tools.gmail.get_thread import (
    GmailGetThread as GetThreadTool,
    GetThreadSchema,
)
from langchain.tools.gmail.search import GmailSearch as SearchTool
from langchain.tools.gmail.send_message import (
    GmailSendMessage as SendMessageTool,
)
from langchain.tools.gmail.utils import get_gmail_credentials, build_resource_service
from pydantic import BaseModel, Field

from beebot.config import Config
from beebot.packs.system_base_pack import SystemBasePack


# For all of these packs, see: https://developers.google.com/gmail/api/quickstart/python for how to authenticate


def credentials(config: Config):
    return get_gmail_credentials(
        scopes=["https://mail.google.com/"],
        client_secrets_file=config.gmail_credentials_file,
    )


def api_resource(config: Config):
    return build_resource_service(credentials=credentials(config))


class MessageSchema(BaseModel):
    """The LangChain schema doesn't convert to OpenAI functions"""

    message: str = Field(
        ...,
        description="The content to include in the message.",
    )
    to: str = Field(
        ...,
        description="The comma-separated list of recipients.",
    )
    subject: str = Field(
        ...,
        description="The subject of the message.",
    )
    cc: str = Field(
        None,
        description="The comma-separated list of CC recipients.",
    )
    bcc: str = Field(
        None,
        description="The comma-separated list of BCC recipients.",
    )


class CreateDraft(SystemBasePack):
    name = "gmail_create_draft"
    description = "Use Gmail to create a draft email inside of Gmail."
    args_schema = MessageSchema
    categories = ["Email"]

    def _run(self, *args, **kwargs):
        if to_value := kwargs.get("to"):
            kwargs["to"] = to_value.split(",")
        if to_value := kwargs.get("cc"):
            kwargs["cc"] = to_value.split(",")
        if to_value := kwargs.get("bcc"):
            kwargs["bcc"] = to_value.split(",")

        tool = CreateDraftTool(api_resource=api_resource(self.body.config))
        return tool._run(*args, **kwargs)


class GetMessage(SystemBasePack):
    name = "gmail_get_message"
    description = "Get a Gmail message"
    args_schema = SearchArgsSchema
    categories = ["Email"]
    depends_on = ["gmail_get_thread", "gmail_search"]

    def _run(self, *args, **kwargs):
        tool = GetMessageTool(api_resource=api_resource(self.body.config))
        return tool._run(*args, **kwargs)


class GetThread(SystemBasePack):
    name = "gmail_get_thread"
    description = "Get a Gmail thread"
    args_schema = GetThreadSchema
    categories = ["Email"]
    depends_on = ["gmail_get_message", "gmail_search"]

    def _run(self, *args, **kwargs):
        tool = GetThreadTool(api_resource=api_resource(self.body.config))
        return tool._run(*args, **kwargs)


class Search(SystemBasePack):
    name = "gmail_search"
    description = "Search for Gmail messages and threads"
    args_schema = SearchArgsSchema
    categories = ["Email"]
    depends_on = ["gmail_get_thread", "gmail_get_message"]

    def _run(self, *args, **kwargs):
        tool = SearchTool(api_resource=api_resource(self.body.config))
        return tool._run(*args, **kwargs)


class SendMessage(SystemBasePack):
    name = "gmail_send_message"
    description = "Send an email with Gmail"
    args_schema = MessageSchema
    categories = ["Email"]

    reversible = False

    def _run(self, *args, **kwargs):
        if to_value := kwargs.get("to"):
            kwargs["to"] = to_value.split(",")
        if to_value := kwargs.get("cc"):
            kwargs["cc"] = to_value.split(",")
        if to_value := kwargs.get("bcc"):
            kwargs["bcc"] = to_value.split(",")

        tool = SendMessageTool(api_resource=api_resource(self.body.config))
        return tool._run(*args, **kwargs)
