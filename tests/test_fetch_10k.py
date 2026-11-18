from pathlib import Path
from typing import Any

import pytest
import requests
import responses

from edgar_10k import edgar
from edgar_10k.cli import fetch_10k_report_from

AAPL_ACCESSION = "0000320193-25-000079"
AAPL_DOCUMENT = "aapl-20250927.htm"
LOGO = (Path(__file__).parent / "fixtures" / "logo.png").read_bytes()


def filing(form: str, date: str, accession: str = AAPL_ACCESSION, document: str = AAPL_DOCUMENT) -> dict[str, str]:
    return {"form": form, "filingDate": date, "accessionNumber": accession, "primaryDocument": document}


def submissions(*filings: dict[str, str]) -> dict[str, Any]:
    keys = ("form", "filingDate", "accessionNumber", "primaryDocument")
    return {"name": "Test Corp", "filings": {"recent": {key: [f[key] for f in filings] for key in keys}}}


def serve_10k(sec: responses.RequestsMock, cik: int, accession: str, document: str, html: str) -> None:
    sec.add(
        responses.GET,
        edgar.SUBMISSIONS_URL.format(cik=cik),
        json=submissions(filing("10-K", "2025-10-31", accession, document)),
    )
    sec.add(responses.GET, edgar.build_filing_url(cik, accession, document), body=html)
    sec.add(responses.GET, edgar.build_filing_url(cik, accession, "logo.png"), body=LOGO, content_type="image/png")


def test_requests_carry_the_declared_user_agent(sec: responses.RequestsMock) -> None:
    edgar.fetch_companies()

    assert sec.calls[0].request.headers["User-Agent"] == "Maxime Pierron maxime.pierron@outlook.com"


@pytest.mark.usefixtures("sec")
def test_get_cik_returns_the_cik_of_the_ticker() -> None:
    assert edgar.get_cik(edgar.fetch_companies(), "MSFT") == 789019


@pytest.mark.usefixtures("sec")
def test_get_cik_fails_fast_on_unknown_ticker() -> None:
    with pytest.raises(ValueError, match="NOPE"):
        edgar.get_cik(edgar.fetch_companies(), "NOPE")


def test_submissions_are_requested_with_a_ten_digits_cik(sec: responses.RequestsMock) -> None:
    sec.add(responses.GET, "https://data.sec.gov/submissions/CIK0000320193.json", json={"name": "Apple Inc."})

    assert edgar.fetch_submissions(320193) == {"name": "Apple Inc."}


def test_submissions_fail_fast_on_unknown_cik(sec: responses.RequestsMock) -> None:
    sec.add(responses.GET, edgar.SUBMISSIONS_URL.format(cik=1), status=404)

    with pytest.raises(requests.HTTPError, match="404"):
        edgar.fetch_submissions(1)


def test_latest_10k_picks_the_most_recently_filed_strict_10k() -> None:
    data = submissions(
        filing("10-K", "2023-11-03", "0000320193-23-000106", "aapl-20230930.htm"),
        filing("10-K/A", "2025-12-01", "0000320193-25-000099", "aapl-amendment.htm"),
        filing("10-K", "2025-10-31", AAPL_ACCESSION, AAPL_DOCUMENT),
        filing("10-Q", "2026-02-01", "0000320193-26-000006", "aapl-20251227.htm"),
        filing("10-K", "2024-11-01", "0000320193-24-000123", "aapl-20240928.htm"),
    )

    assert edgar.latest_10k(data) == (AAPL_ACCESSION, AAPL_DOCUMENT)


def test_latest_10k_fails_fast_when_no_10k_was_filed() -> None:
    data = submissions(filing("10-Q", "2026-02-01"), filing("10-K/A", "2025-12-01"), filing("10-KT", "2025-06-01"))

    with pytest.raises(LookupError, match="Test Corp"):
        edgar.latest_10k(data)


def test_filing_url_has_no_leading_zeros_in_cik_and_no_dashes_in_accession() -> None:
    assert edgar.build_filing_url(320193, AAPL_ACCESSION, AAPL_DOCUMENT) == (
        "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm"
    )


def test_fetched_html_is_a_real_document(sec: responses.RequestsMock, filing_html: str) -> None:
    url = edgar.build_filing_url(320193, AAPL_ACCESSION, AAPL_DOCUMENT)
    sec.add(responses.GET, url, body=filing_html)

    html = edgar.fetch_html(url)

    assert "<div" in html
    assert len(html.encode()) > 1024


def test_one_pdf_per_ticker_named_after_the_ticker(
    sec: responses.RequestsMock, filing_html: str, tmp_path: Path
) -> None:
    serve_10k(sec, 320193, AAPL_ACCESSION, AAPL_DOCUMENT, filing_html)
    serve_10k(sec, 789019, "0000950170-25-100235", "msft-20250630.htm", filing_html)
    dest = tmp_path / "reports"

    fetch_10k_report_from(["--tickers", "aapl,MSFT", "--dest", str(dest)])

    pdfs = sorted(dest.glob("*.pdf"))
    assert [pdf.name for pdf in pdfs] == ["aapl-20250927.pdf", "msft-20250630.pdf"]
    for pdf in pdfs:
        assert pdf.stat().st_size > 0
        assert pdf.read_bytes().startswith(b"%PDF")


def test_pdf_goes_to_the_current_directory_without_dest(
    sec: responses.RequestsMock, filing_html: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    serve_10k(sec, 320193, AAPL_ACCESSION, AAPL_DOCUMENT, filing_html)
    monkeypatch.chdir(tmp_path)

    fetch_10k_report_from(["--tickers", "AAPL"])

    assert [pdf.name for pdf in tmp_path.glob("*.pdf")] == ["aapl-20250927.pdf"]


def test_unknown_ticker_gathers_errors_keep_going(sec: responses.RequestsMock, filing_html: str, tmp_path: Path) -> None:
    serve_10k(sec, 320193, AAPL_ACCESSION, AAPL_DOCUMENT, filing_html)
    serve_10k(sec, 789019, "0000950170-25-100235", "msft-20250630.htm", filing_html)

    with pytest.raises(SystemExit):
        fetch_10k_report_from(["--tickers", "AAPL,NOPE,MSFT", "--dest", str(tmp_path)])

    assert sorted(p.name for p in tmp_path.glob("*.pdf")) == ["aapl-20250927.pdf", "msft-20250630.pdf"]


def test_unknown_cik_gathers_errors_keep_going(sec: responses.RequestsMock, tmp_path: Path) -> None:
    sec.add(responses.GET, edgar.SUBMISSIONS_URL.format(cik=320193), status=404)

    with pytest.raises(SystemExit):
        fetch_10k_report_from(["--tickers", "AAPL", "--dest", str(tmp_path)])

    assert list(tmp_path.glob("*.pdf")) == []


def test_company_without_10k_gathers_errors_keep_going(sec: responses.RequestsMock, tmp_path: Path) -> None:
    sec.add(responses.GET, edgar.SUBMISSIONS_URL.format(cik=320193), json=submissions(filing("10-Q", "2026-02-01")))

    with pytest.raises(SystemExit):
        fetch_10k_report_from(["--tickers", "AAPL", "--dest", str(tmp_path)])

    assert list(tmp_path.glob("*.pdf")) == []


def test_images_of_the_filing_are_downloaded_with_the_declared_user_agent(
    sec: responses.RequestsMock, filing_html: str, tmp_path: Path
) -> None:
    serve_10k(sec, 320193, AAPL_ACCESSION, AAPL_DOCUMENT, filing_html)

    fetch_10k_report_from(["--tickers", "AAPL", "--dest", str(tmp_path)])

    image_url = edgar.build_filing_url(320193, AAPL_ACCESSION, "logo.png")
    image_calls = [call for call in sec.calls if call.request.url == image_url]
    assert len(image_calls) == 1
    assert image_calls[0].request.headers["User-Agent"] == edgar.USER_AGENT


def test_image_that_cannot_be_downloaded_gathers_errors_keep_going(
    sec: responses.RequestsMock, filing_html: str, tmp_path: Path
) -> None:
    serve_10k(sec, 320193, AAPL_ACCESSION, AAPL_DOCUMENT, filing_html)
    sec.replace(responses.GET, edgar.build_filing_url(320193, AAPL_ACCESSION, "logo.png"), status=403)

    with pytest.raises(SystemExit):
        fetch_10k_report_from(["--tickers", "AAPL", "--dest", str(tmp_path)])

    assert list(tmp_path.glob("*.pdf")) == []
