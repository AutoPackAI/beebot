import aiohttp
import requests
from autopack import Pack
from pydantic import BaseModel, Field

PACK_DESCRIPTION = (
    "Retrieves the raw HTML content of a specified webpage. It is useful when you specifically require access to the "
    "raw HTML of a webpage, and are not interested in its text contents."
)


class GetHtmlContentArgs(BaseModel):
    url: str = Field(
        ...,
        description="The URL of the webpage from which to retrieve the HTML content.",
    )


class GetWebpageHtmlContent(Pack):
    name = "get_webpage_html_content"
    description = PACK_DESCRIPTION
    args_schema = GetHtmlContentArgs
    categories = ["Web"]
    dependencies = ["requests", "aiohttp"]

    filter_threshold: int = Field(
        default=0,
        description="If given a non-zero value will return only the first N characters",
    )

    def _run(self, url: str) -> str:
        response = requests.get(url)
        if self.filter_threshold:
            return response.text[: self.filter_threshold]
        return response.text

    async def _arun(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                text = await response.text()
                if self.filter_threshold:
                    return text[: self.filter_threshold]
                return text
