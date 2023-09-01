import os
from unittest.mock import patch

from wolframalpha_query import WolframAlphaQuery


def test_wolframalpha_no_appid():
    pack = WolframAlphaQuery()
    assert "not supported" in pack.run(query="population of united states")


def test_wolframalpha_with_appid():
    os.environ["WOLFRAM_ALPHA_APPID"] = "1234"
    pack = WolframAlphaQuery()

    with patch("langchain.WolframAlphaAPIWrapper.run") as mock_load:
        mock_load.return_value = "331.9 million"
        assert "331.9 million" in pack.run(query="population of united states")
