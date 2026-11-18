from collections.abc import Iterator
from pathlib import Path

import pytest
import responses

from edgar_10k.edgar import TICKERS_URL

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sec() -> Iterator[responses.RequestsMock]:
    """Mocked SEC API, already serving the company_tickers.json fixture."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        mock.add(responses.GET, TICKERS_URL, body=(FIXTURES / "company_tickers.json").read_text())
        yield mock


@pytest.fixture
def filing_html() -> str:
    return (FIXTURES / "filing.htm").read_text()
