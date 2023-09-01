from unittest.mock import patch

import pytest
from langchain.schema import Document

from wikipedia_summarize import WikipediaPack


def test_sync_llm():
    def mock_llm(text_in: str):
        return text_in.strip().split("\n")[-1]

    pack = WikipediaPack(llm=mock_llm)
    with patch("langchain.WikipediaAPIWrapper.load") as mock_load:
        # Set the return value of the mock object
        page = Document(page_content="Page content", metadata={"title": "A page"})
        mock_load.return_value = [page]

        assert pack.run(query="some text", question="asdf") == "Page content"


@pytest.mark.asyncio
async def test_async_llm():
    async def mock_llm(text_in: str):
        return text_in.strip().split("\n")[-1]

    pack = WikipediaPack(allm=mock_llm)
    with patch("langchain.WikipediaAPIWrapper.load") as mock_load:
        # Set the return value of the mock object
        page = Document(page_content="Page content", metadata={"title": "A page"})
        mock_load.return_value = [page]

        assert await pack.arun(query="some text", question="asdf") == "Page content"
