import pytest

from extract_information_from_webpage.extract_information_from_webpage import (
    ExtractInformationFromWebpage,
)


def mock_llm(text_in: str):
    return text_in.upper()


async def mock_allm(text_in: str):
    return text_in.upper()


def test_analyze_webpage_content_sync_no_information():
    pack = ExtractInformationFromWebpage(llm=mock_llm)
    results = pack.run(url="https://www.bbc.com/news")
    assert "SPECIFIC QUESTION" not in results
    assert "PROVIDE A SUMMARY" in results
    assert "BBC" in results


def test_analyze_webpage_content_sync_information():
    pack = ExtractInformationFromWebpage(llm=mock_llm)
    results = pack.run(
        url="https://www.bbc.com/news", information="What are the top headlines?"
    )
    assert "SPECIFIC QUESTION" in results
    assert "BBC" in results


@pytest.mark.asyncio
async def test_analyze_webpage_content_async_no_information():
    pack = ExtractInformationFromWebpage(allm=mock_allm)
    results = await pack.arun(url="https://www.bbc.com/news")
    assert "SPECIFIC QUESTION" not in results
    assert "PROVIDE A SUMMARY" in results
    assert "BBC" in results


@pytest.mark.asyncio
async def test_analyze_webpage_content_async_information():
    pack = ExtractInformationFromWebpage(allm=mock_allm)
    results = await pack.arun(
        url="https://www.cambridge.org/core/journals/business-and-politics/article/future-of-ai-is-in-the-states-the"
        "-case-of-autonomous-vehicle-policies/D6F0B764A976C2A934D517AE1D781195",
        information="key findings",
    )
    assert "KEY FINDINGS" in results
    assert "CAMBRIDGE" in results
