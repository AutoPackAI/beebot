import requests
from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack
from beebot.tool_filters import filter_long_documents

PACK_NAME = "get_html_content"
PACK_DESCRIPTION = (
    "Retrieves the HTML content of a specified webpage. It is useful when you specifically require access to the raw "
    "HTML of a webpage, and are not interested in its text contents."
)


class GetHtmlContentArgs(BaseModel):
    url: str = Field(
        ...,
        description="The URL of the webpage from which to retrieve the HTML content.",
    )


class GetHtmlContent(SystemBasePack):
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = GetHtmlContentArgs
    categories = ["Web"]

    def _run(self, url: str) -> str:
        response = requests.get(url)
        return filter_long_documents(self.body, response.text)
