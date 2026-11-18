import argparse
import json
import sys
from pathlib import Path

import requests

from edgar_10k import edgar


def find_ticker(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Find the companies whose title matches a name.")
    parser.add_argument("--name", required=True, help="Part of the company title, e.g. apple")
    args = parser.parse_args(argv)

    matches = edgar.search_by_title(edgar.fetch_companies(), args.name)
    if matches:
        print(json.dumps(matches, indent=2))
    else:
        print(f"Warning: No company found for '{args.name}'", file=sys.stderr)


def fetch_10k_report_from(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Fetch the latest 10-K of each ticker and save it as a PDF.")
    parser.add_argument("--tickers", required=True, help="Comma separated tickers, e.g. AAPL,MSFT")
    parser.add_argument("--dest", default=".", help="Destination folder (default: current directory)")
    args = parser.parse_args(argv)

    tickers = [ticker.strip().upper() for ticker in args.tickers.split(",")]
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    companies = edgar.fetch_companies()
    results: dict[str, str] = {}
    for ticker in tickers:
        try:
            cik = edgar.get_cik(companies, ticker)
            accession, document = edgar.latest_10k(edgar.fetch_submissions(cik))
            url = edgar.build_filing_url(cik, accession, document)
            pdf_name = Path(document).stem
            edgar.html_to_pdf(edgar.fetch_html(url), url, dest / f"{pdf_name}.pdf")
            results[ticker] = "Success"
        except (ValueError, LookupError, requests.RequestException) as error:
            results[ticker] = f"Failed ({error})"

    for ticker, result in results.items():
        print(f"{ticker}: {result}")

    successful = sum(result == "Success" for result in results.values())
    print(f"\n{successful}/{len(tickers)} reports downloaded.")
    return_code = 0 if successful == len(tickers) else 1
    if return_code:
        raise SystemExit(return_code)
