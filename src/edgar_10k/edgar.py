from pathlib import Path
from typing import Any

import requests
from playwright.sync_api import Route, sync_playwright

USER_AGENT = "Maxime Pierron maxime.pierron@outlook.com"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
FILING_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"


def _get(url: str) -> requests.Response:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    return response


def fetch_companies() -> list[dict[str, Any]]:
    data: dict[str, dict[str, Any]] = _get(TICKERS_URL).json()
    return list(data.values())


def search_by_title(companies: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    return [company for company in companies if name.lower() in company["title"].lower()]


def get_cik(companies: list[dict[str, Any]], ticker: str) -> int:
    for company in companies:
        if company["ticker"] == ticker:
            return int(company["cik_str"])
    raise ValueError(f"Unknown ticker: {ticker}")


def fetch_submissions(cik: int) -> dict[str, Any]:
    submissions: dict[str, Any] = _get(SUBMISSIONS_URL.format(cik=cik)).json()
    return submissions


def latest_10k(submissions: dict[str, Any]) -> tuple[str, str]:
    """Return (accessionNumber, primaryDocument) of the most recently filed 10-K."""
    recent = submissions["filings"]["recent"]
    filings_fields = [recent["form"], recent["filingDate"], recent["accessionNumber"], recent["primaryDocument"]]
    n = len(recent["form"])
    if not all(len(x) == n for x in filings_fields):
        raise ValueError("Inconsistent filing data: SEC submission fields have different lengths")
    filings = zip(*filings_fields)
    ten_ks = [(date, accession, document) for form, date, accession, document in filings if form == "10-K"]
    if not ten_ks:
        raise LookupError(f"No 10-K filed by {submissions['name']}")
    _, accession, document = max(ten_ks)
    return accession, document


def build_filing_url(cik: int, accession: str, document: str) -> str:
    return FILING_URL.format(cik=cik, accession=accession.replace("-", ""), document=document)


def fetch_html(url: str) -> str:
    return _get(url).text


def html_to_pdf(html: str, url: str, pdf_path: Path) -> None:
    errors: list[requests.RequestException] = []

    def serve(route: Route) -> None:
        # The page is the html already fetched; its other sec.gov resources (images) are downloaded
        # the same way as the html, with the declared User-Agent, instead of by Chromium itself.
        if route.request.url == url:
            route.fulfill(body=html, content_type="text/html; charset=utf-8")
            return
        try:
            response = _get(route.request.url)
        except requests.RequestException as error:
            errors.append(error)
            route.abort()
        else:
            route.fulfill(body=response.content, content_type=response.headers["Content-Type"])

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.route("https://www.sec.gov/**", serve)
            page.goto(url)
            if errors:
                raise errors[0]
            page.pdf(path=pdf_path, format="A4", print_background=True)
            if errors:
                raise errors[0]
        finally:
            browser.close()
