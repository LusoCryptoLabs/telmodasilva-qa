# telmodasilva-qa

[![tests](https://github.com/LusoCryptoLabs/telmodasilva-qa/actions/workflows/tests.yml/badge.svg)](https://github.com/LusoCryptoLabs/telmodasilva-qa/actions/workflows/tests.yml)

Test automation for my personal site and course library. Python, pytest and Playwright. It
runs against production on every push and every morning at 06:17 UTC.

Latest report: https://lusocryptolabs.github.io/telmodasilva-qa/

## What it covers

| Layer | Checks | Tools |
|---|---|---|
| API | Both write endpoints reject bad input with the documented error, and GET is refused | httpx |
| HTTP | HTTPS and www redirects, security headers, real 404s, robots.txt, every sitemap URL served directly | httpx |
| Content | Every page in the sitemap: one title, a description, canonical, one h1, indexable, `lang`, share image; titles and descriptions unique | httpx, html.parser |
| Layout | No horizontal scroll at 320, 360, 390 and 414 px on the key pages | Playwright |
| Runtime | No console errors and no failed requests while the key pages load | Playwright |
| Analytics | One page view per load, a stable visitor id, and the owner opt-out sends nothing | Playwright |
| Accessibility | No serious or critical WCAG 2.1 AA violations | axe-core |
| End to end | The graded Python challenge of course 1: starter code, false positives, false negatives, syntax error, infinite loop, and a passing solution that is remembered after reload | Playwright, Pyodide in the page |

The content tests are generated from the live sitemap, so a new page is covered the day it is
published.

## What it found

The first run, on 2026-10-23, found five problems on the site. Three are fixed and covered by
normal tests now. The fix for `lang` split the app into two route groups, each with its own
root layout, so the server HTML carries the right language.

| Area | Issue | Status |
|---|---|---|
| Content | English pages declared `lang="pt"` | fixed 2026-10-23 |
| Content | English pages had no `og:image` | fixed 2026-10-23 |
| Accessibility | The code editor of the graded challenge had no accessible name | fixed 2026-10-23 |
| Accessibility | The light suffix in the logo is below 4.5:1 contrast | open |
| Accessibility | Links inside paragraphs are told apart by colour only | open |

The two open issues change how the site looks, so they wait for a design decision. Until then
they are listed in `tests/a11y/test_axe.py` with the reason, and a page that has only those
is reported as xfail. Any other serious violation fails the run.

## Safe to run against production

- Every API request is invalid on purpose. The server rejects it before writing anything.
- `/api/analytics` is stubbed in the browser, including `sendBeacon` calls. Test runs are not
  counted as visits.
- The passing solution of the graded challenge is not in this repository. It comes from the
  `CHALLENGE_SOLUTION` secret; without it that test is skipped. CI keeps no traces or
  screenshots, because the editor would show the solution.

## Run it

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run playwright install chromium
uv run pytest -n 4
```

Pick a layer with a marker, or point the suite at another environment:

```bash
uv run pytest -m api
uv run pytest -m "ui or e2e" --headed
uv run pytest --base-url http://localhost:3000
```

Outside production, the redirect and security header checks are skipped: those come from the
proxy in front of the app, not from the app.

Markers: `api`, `content`, `ui`, `a11y`, `e2e`.

## Layout

```
qa/
  site.py                 key pages, phone widths, sitemap reader
  html_head.py            head parser (ignores <title> inside inline SVGs)
  pages/python_challenge.py   page object for the graded challenge
tests/
  api/                    endpoint contracts, HTTP behaviour
  content/                per-page metadata from the sitemap
  ui/                     layout, runtime errors, analytics
  a11y/                   axe-core scan
  e2e/                    graded Python challenge
scripts/summary.py        JUnit to Markdown for the CI job page
```
