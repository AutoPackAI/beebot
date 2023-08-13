from html_request.http_request import HttpRequest


def test_http_request_get():
    url = "https://google.com"
    pack = HttpRequest()
    response = pack.run(url=url)
    assert "Google Search" in response


def test_http_request_get():
    url = "https://google.com"
    pack = HttpRequest()
    response = pack.run(url=url)
    assert "Google Search" in response
