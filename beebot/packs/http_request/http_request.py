import json

import aiohttp
import requests
from autopack import Pack
from pydantic import BaseModel, Field

PACK_DESCRIPTION = (
    "Makes an HTTP request and returns the raw response. This function should be used for basic GET or "
    "POST requests and is not intended for fetching web pages or performing complex operations."
)


class HttpRequestArgs(BaseModel):
    url: str = Field(..., description="URL of the resource to request.")
    method: str = Field(
        description="The HTTP method to use for the request (e.g., GET, POST). Defaults to GET.",
        default="GET",
    )
    data: str = Field(description="Data to send with the request (for POST requests).", default="")
    headers: str = Field(
        description="JSON Encoded headers to include in the request.",
        default_factory=dict,
    )


class HttpRequest(Pack):
    name = "http_request"
    description = PACK_DESCRIPTION
    args_schema = HttpRequestArgs
    categories = ["Web"]

    def _run(self, url: str, method: str = "GET", data: str = None, headers: str = None) -> str:
        headers_dict = {}
        if headers:
            headers_dict = json.loads(headers)
        response = requests.request(method, url, headers=headers_dict, data=data)
        return f"HTTP Response {response.status_code}: {response.content}"

    async def _arun(self, url: str, method: str = "GET", data: str = None, headers: str = None) -> str:
        headers_dict = {}
        if headers:
            headers_dict = json.loads(headers)

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, data=data, headers=headers_dict) as response:
                text = await response.text()
                return f"HTTP Response {response.status}: {text}"
