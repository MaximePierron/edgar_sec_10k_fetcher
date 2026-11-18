The first hour was spent in reconnaissance so to say. I figured out how to access the 10-K and how to build the 10-K html url.
The findings and first strategy are reflected in the first prompt I fed Claude.
I used Claude to generate the initial implementation based on the architecture I had in mind. I then reviewed, tested and modified the generated code as I encountered issues and reconsidered some of the initial design decisions.


Following Claude's questions, I first assumed that I should abort if there is an error while fetching a document for one of the companies in the list while still allowing partial success. On this topic, I actually went back on this decision and figured that the user could potentially wish to get all the successful files. The different prints in `fetch_10k_report_from` are reflecting what a pop-up window on the front-end could show with an overview of the successes and failures or waht the response of an API call could contain.


As suggested by Claude, I had in mind to use fixtures for the tests for multiple reasons:
- Being reproducible, the tests don't depend on SEC availability.
- Moderate requests to minimize server load as suggested by the SEC.
- Being deterministic, I keep control exactly over what the API returns, including errors and edge cases.


At this stage, plus a minor tweak in the Playwright installation of Chromium, I was very satisfied that I had an already working solution on first implementation, as the task description does not consider missing images an automatic fail. I had then the time to precisely look at the image issue and the tests and push the architecture a bit further and add robustness.


Using Playwright to convert an HTML page into a PDF file was a first for me and as the prompt logs will show I got confronted to the image not being rendered in my files. I had the intuition that they could not be loaded by Playwright and looking at the working fix Claude returned the error was to rely on Playwright's Chromium to fetch those images. The solution is therefore to also intercept the resources requests to the SEC API call and actually rely on python and requests and the proper User Agent to fulfil the requests (html and images) for Chromium.


I chose a CLI because it provides a straightforward way to run the workflow locally, specify the target companies and output directory, and save the generated PDFs directly to disk. It also makes the process very easy to repeat. I feel like setting up a whole web API would have just added complexity and not much value.
On this subject, even though CIKs are proper SEC identifiers, I went for the tickers in `fetch_10k_report_from` as I figured that the CIK were not necessarily a very user friendly value in the CLI. Realistically, with a proper frontend any value could fly (title, CIK, ticker) with the proper dropdown suggestions and with an API both the CIKs and tickers could be used. The titles were not a safe value; there are multiple companies with apple in their title for example and one does not necessarily know that Apple is Apple Inc. Even then, the title (for a strict API call without frontend) is not robust enough and would lead to unnecessary failures.


The code is slightly different from what Claude produced first. I made sure the browser is always closed at the end of my use of Playwright. I rewrote the code to allow the fetching of the 10-Ks even if one has failed and rewrote the tests accordingly. To add robustness in the code, I made sure that the `filings` values I am zipping are all of the same length.


As the project is small and has this POC vibe, I chose to not deploy a Docker container but rather use a very neat python tool called `uv` that I really affectionate. It is very good for environment management, dependency resolution, cache management, reproducibility with lockfiles.


Also as it is a python project, I decided to use `ruff` and `mypy` for linting and formatting and type safety which for me are absolutely required for any professional python project.

Overall, I worked around 4 hours on the task:
- 1 hour on the 16th to elaborate the architecture
- 1 hour on the 17th in the morning to debug and rework the initial implementation
- 1 hour on the 17th in the afternoon to fix the broken images, rework part of the code and test
- 1 hour on the 18th in the morning to have a look one more time at the tests, write these notes and push to github.


The solution I am presenting now returns decently sized PDF files with working links and images. Out of the 6 companies listed, Goldman Sachs is the one where I have grievances as I have every an empty or almost empty page every few pages. It is not catastrophic, the page number is not doubled or anything and so because of the time constraint and the fact that the 5 others are rather satysfying I did not push further. In my opinion, the Playwright parameters could probably be tuned to fix this or some pdf library down the line could get rid of those empty pages. 