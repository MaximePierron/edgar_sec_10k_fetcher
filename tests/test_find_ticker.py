import json

import pytest

from edgar_10k.cli import find_ticker


@pytest.mark.usefixtures("sec")
def test_name_returns_the_matching_companies_as_json(capsys: pytest.CaptureFixture[str]) -> None:
    find_ticker(["--name", "apple"])

    assert json.loads(capsys.readouterr().out) == [
        {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        {"cik_str": 1418121, "ticker": "APLE", "title": "Apple Hospitality REIT, Inc."},
    ]


@pytest.mark.usefixtures("sec")
def test_unknown_name_warns_without_raising(capsys: pytest.CaptureFixture[str]) -> None:
    find_ticker(["--name", "doesnotexist"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "No company found" in captured.err


@pytest.mark.usefixtures("sec")
def test_only_the_title_is_matched_not_the_ticker(capsys: pytest.CaptureFixture[str]) -> None:
    find_ticker(["--name", "AAPL"])

    assert "No company found" in capsys.readouterr().err
