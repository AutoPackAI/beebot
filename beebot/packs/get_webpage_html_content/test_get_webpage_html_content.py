import pytest

from get_webpage_html_content.get_webpage_html_content import GetWebpageHtmlContent


def test_webpage_html_content_with_filter():
    # Just a random site with a lot of text
    url = "https://en.wikipedia.org/wiki/World_War_II"
    pack = GetWebpageHtmlContent(filter_threshold=2000)
    response = pack.run(url=url)
    assert len(response) == 2000


def test_webpage_html_content_without_filter():
    # Just a random site with a lot of text
    url = "https://en.wikipedia.org/wiki/World_War_II"
    pack = GetWebpageHtmlContent()
    response = pack.run(url=url)
    assert len(response) > 2000


@pytest.mark.asyncio
async def test_aget_webpage_html_content_with_filter():
    # Just a random site with a lot of text
    url = "https://en.wikipedia.org/wiki/World_War_II"
    pack = GetWebpageHtmlContent(filter_threshold=2000)
    response = await pack.arun(url=url)
    assert len(response) == 2000


@pytest.mark.asyncio
async def test_aget_webpage_html_content_without_filter():
    # Just a random site with a lot of text
    url = "https://en.wikipedia.org/wiki/World_War_II"
    pack = GetWebpageHtmlContent()
    response = await pack.arun(url=url)
    assert len(response) > 2000
