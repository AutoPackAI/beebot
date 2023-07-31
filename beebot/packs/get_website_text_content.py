import re

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack
from beebot.tool_filters.filter_long_documents import filter_long_documents

PACK_NAME = "get_website_content"
PACK_DESCRIPTION = (
    "Retrieves the text content of a specified webpage. It is useful when you want to obtain the textual information "
    "from a webpage without the need for in-depth analysis."
)


class GetWebsiteTextContentArgs(BaseModel):
    url: str = Field(
        ...,
        description="The URL of the webpage from which to retrieve the text content.",
    )


class GetWebsiteTextContent(SystemBasePack):
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = GetWebsiteTextContentArgs
    categories = ["Web"]

    def _run(self, url: str) -> str:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        stripped_text = re.sub(r"\s+", " ", soup.get_text().strip())
        return filter_long_documents(self.body, stripped_text)
