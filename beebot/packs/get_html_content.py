from typing import Type

import requests
from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "get_html_content"
PACK_DESCRIPTION = (
    "Retrieves the HTML content of a specified webpage. It is useful when you specifically require access to the raw "
    "HTML of a webpage, without the need for text analysis."
)


class GetHtmlContentArgs(BaseModel):
    url: str = Field(
        ...,
        description="The URL of the webpage from which to retrieve the HTML content.",
    )


class GetHtmlContent(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = GetHtmlContentArgs
    categories: list[str] = ["Web"]

    def _run(self, url: str) -> str:
        response = requests.get(url)
        return response.text
