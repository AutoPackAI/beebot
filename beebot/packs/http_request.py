import json
from typing import Type

import requests
from pydantic import BaseModel, Field

from beebot.packs.system_base_pack import SystemBasePack

PACK_NAME = "http_request"
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
    data: str = Field(description="Data to send with the request (for POST requests).")
    headers: str = Field(description="JSON Encoded headers to include in the request.")


class HttpRequest(SystemBasePack):
    name: str = PACK_NAME
    description: str = PACK_DESCRIPTION
    args_schema: Type[BaseModel] = HttpRequestArgs
    categories: list[str] = ["Files"]

    def _run(
        self, url: str, method: str = "GET", data: str = None, headers: str = None
    ):
        headers_dict = {}
        if headers:
            headers_dict = json.loads(headers)
        response = requests.request(method, url, headers=headers_dict, data=data)
        return f"HTTP Response {response.status_code}: {response.content}"
