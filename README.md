# edgar-10k

Fetch the latest 10-K of companies from SEC EDGAR and save each one as a PDF.

PDF conversion uses Playwright (headless Chromium): hyperlinks stay clickable in the PDF and relative links are
resolved against the SEC filing URL, so there are no dead links.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run playwright install chromium
```

## Usage

Find a ticker from (part of) a company name:

```bash
uv run find_ticker --name "apple"
```

Fetch the latest 10-K of each ticker as `<ticker_10k_filing_date>.pdf` (in the current directory, or in `--dest`):

```bash
uv run fetch_10k_report_from --tickers AAPL,META,GOOGL,AMZN,NFLX,GS --dest reports
```

The run keeps going when facing errors (unknown ticker, unknown CIK, no 10-K filed) and displays an overview of the results.

## Tests and checks

```bash
uv run pytest
uv run ruff check .
uv run mypy .
```
