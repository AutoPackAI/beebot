import os
from unittest.mock import patch

import pytest

from google_search import GoogleSearch


def test_search_no_api_key():
    results = GoogleSearch().run(query="bbc news website")
    assert "not supported" in results


def test_search_sync():
    os.environ["SERPER_API_KEY"] = "1234"
    with patch("langchain.GoogleSerperAPIWrapper.results") as mock_load:
        mock_load.return_value = {
            "organic": [
                {
                    "link": "https://www.bbc.com/news",
                    "snippet": "Visit BBC News for up-to-the-minute news, breaking news, video, audio and feature "
                    "stories. BBC News provides trusted World and UK news as well as local and ...",
                },
            ]
        }
        results = GoogleSearch().run(query="bbc news website")

    assert "https://www.bbc.com/news" in results
    assert "breaking news" in results


@pytest.mark.asyncio
async def test_search_async():
    async def async_results(self, query):
        return {
            "organic": [
                {
                    "link": "https://www.bbc.com/news",
                    "snippet": "Visit BBC News for up-to-the-minute news, breaking news, video, audio and feature "
                    "stories. BBC News provides trusted World and UK news as well as local and ...",
                },
            ]
        }

    os.environ["SERPER_API_KEY"] = "1234"
    with patch(
        "langchain.GoogleSerperAPIWrapper.aresults", new=async_results
    ) as mock_load:
        results = await GoogleSearch().arun(query="bbc news website")

    assert "https://www.bbc.com/news" in results
    assert "breaking news" in results
