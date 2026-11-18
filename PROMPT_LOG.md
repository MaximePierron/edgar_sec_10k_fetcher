# Prompt log: edgar-10k

- **Project:** fetch the latest 10-K of a list of companies from SEC EDGAR and save each as a PDF
- **Date (time 0):** Tuesday, 2026-11-17
- **Log generated:** 2026-11-17 21:29 UTC (sandbox clock)

## About the timestamps

Claude has no clock inside a conversation, so the exact minute of each prompt was not recorded. What is known:

- Every prompt below was sent on **2026-11-17**, in the order listed.
- The first build of the project was zipped at **10:06** (sandbox clock, from the file listing), during the work on prompt 2.
- This log was generated at **21:29 UTC** (sandbox clock), in response to prompt 5.

If you need minute-level times, take them from your chat history; the order and content below are exact.

---

## Prompt 1: project specification (10:57 am)

**Prompt (verbatim):**

```text
Consider this time 0, I am gonna ask you for a full timestamped prompt log at the end of the project.
This project aims at fetching the latest 10-K report for a given list of companies from the EDGAR SEC API.
It will convert each html page that we will eventually access into a pdf file.
Here is the documentation:
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- https://www.sec.gov/search-filings/edgar-application-programming-interfaces

The codebase will be in Python. I want this to run in a terminal, in uv virtual env, I want ruff and mypy basically configured with 120 characters maximum line length.
The unit tests will be written with pytest and should aim at the real responsibility of the methods, no trivial assessment.
For the html to pdf conversion, I was used to pdfkit but it looks it is no longer maintained, people seem to recommend Playwright or Weasyprint, I have no experience with either of those so take the one that is the most adapted according to you, I mostly want to make sure that I don't have dead links in my pdfs.

There will be two terminal functions:
- The first one "find_ticker" will be to get the ticker of the targeted company. The terminal call can take --name as a parameter. The function should print a json of all the possible compatible with either the name or the ticker from this file https://www.sec.gov/files/company_tickers.json in the documentation I gave you. This function should not throw anything if given a value that is not found in the file. It should return a warning of the like "No company found".
- The second function "fetch_10k_report_from" will be the one actually fetching the 10-Ks and converting them in a .pdf file. It will take two parameters --tickers that will be comma separated values turned into a list in the code and an optional --dest to decide where to save the pdfs relative to where the function is being run. For this method, in accordance with the header rules set in the EDGAR SEC documentation, the user agent is gonna be "Maxime Pierron maxime.pierron@outlook.com". Now here is what it is going to do, for each ticker in the list:
	- It will fetch the CIK value linked to this ticker again from https://www.sec.gov/files/company_tickers.json.
	- It is going to fetch the json from this endpoint: https://data.sec.gov/submissions/CIK##########.json. There must be here a fail fast if the CIK is incorrect and we get a 404 Not Found.
	- It is going to extract the 'primaryDocument' and 'accessionNumber' values in 'filings.recent' of the most recently filed 10-K 'form', in this json file each value in each key is related with the same index so to illustrate 'form'[0] has 'accessionNumber'[0] and 'filingDate'[0]. I want the strict 10-K form no variations. It is possible that the company has not yet filed any 10-K so we should also fail fast here.
	- Once you have primaryDocument and accessionNumber you are gonna build a URL: https://www.sec.gov/ix?doc=/Archives/edgar/data/<CIK_WITHOUT_TRAILING_ZEROS>/<ACCESSION_NUMBER_WITHOUT_DASHES>/<PRIMARY_DOCUMENT> and fetch the html file.
	- Then this html will be converted into .pdf file save either where the script has been ran in the terminal or in the given --dest using the ticker as filename.

The unit tests of find_cik should be deterministic, make sure that this value of name returns a specific json. It should also test that a wrong name returns the warning.

The unit tests of fetch_10k_report_from should assess that with a proper CIK the html is not empty, that it contains representative tags like a <div> and be more than 1KB.
It should also check that the pdf is not empty and saved in pytest temp dir with the proper filename, that there is as many pdfs as there were tickers in the list. It should also assess the fail fast are working.

You are gonna produce a minimal yet clear and sufficient README file to explain how to run the code and the tests and the potential packages to install. Follow KISS and YAGNI principles.
It is a rather simple task, the code should reflect this simplicity, do what you have been told, no fluff, no useless null check, no initiative, no extra mile. If anything is still not clear ask me questions now.
```

**Outcome:** no code yet. Claude noted that it cannot give real timestamps and asked five clarifying questions: use the direct Archives URL instead of the `ix?doc=` viewer URL, live tests vs fixtures, abort vs continue on error, how `find_ticker` should match, and whether `find_cik` meant `find_ticker`. It stated assumptions: Playwright, `uv run` entry points, `--dest` defaulting to the current directory.

---

## Prompt 2: answers to the clarifying questions (11:03 am)

**Prompt (verbatim):**

```text
1. yes use the direct url
2. fixtures is good
3. abort
4. I meant name as in title, so only try to match the title
5. I meant find_ticker


Regarding your assumptions for --dest if it is given go for what is given or there are no --dest go for current dir.
```

**Outcome:** built the project (`pyproject.toml`, `src/edgar_10k/edgar.py`, `src/edgar_10k/cli.py`, tests with fixtures, README), delivered as `edgar-10k.zip`. Playwright was chosen for PDF conversion. 17 tests passed in the sandbox, with ruff and mypy clean. Verified that an internal link is kept as a link in the PDF.

---

## Prompt 3: Chromium fails to launch on the user's machine (11:26 am)

**Prompt:**

```text
[pasted traceback]

when I run uv run fetch_10k_report_from --tickers AAPL --dest reports
I get the following logs
```

The pasted traceback ended with `playwright._impl._errors.TargetClosedError: BrowserType.launch: Target page, context or browser has been closed`, caused by `error while loading shared libraries: libnspr4.so: cannot open shared object file`.

**Outcome:** diagnosed as missing Linux system libraries for Chromium (a README gap, not a code bug). Gave the fix `uv run playwright install --with-deps chromium` and added it to the README. Zip re-delivered.

---

## Prompt 4: images missing in the PDFs (12:55 pm)

**Prompt (verbatim):**

````text
The links are working but the images are not printed properly, I think the images are not loaded when the html is converted, I found this code snippet suggested to fix the issue but no success:

```python
        page.wait_for_function("""
            () => {
                const imgs = Array.from(document.images);
                return imgs.every(img => img.complete && img.naturalWidth > 0);
            }
        """)
```
````

**Outcome:** explained that `goto` already waits for the `load` event, so the snippet cannot fix a failed download. Changed `html_to_pdf` so sec.gov images are downloaded with `requests` and the declared User-Agent and handed to Chromium. An image that cannot be downloaded now aborts the run. Added two tests (image fetched with the User-Agent; 403 on an image aborts), bringing the suite to 19 passing tests. The cause was not confirmed against live SEC (no access from the sandbox). Zip re-delivered.

---

## Prompt 5: this log (10:28 pm)

**Prompt (verbatim):**

```text
can you produce a prompt log file of this project ?
```

**Outcome:** this file, `PROMPT_LOG.md`.
