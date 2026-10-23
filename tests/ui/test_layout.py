"""Mobile layout and runtime health of the key pages."""

import pytest
from playwright.sync_api import Page, Request

from qa.site import KEY_PAGES, MOBILE_WIDTHS

pytestmark = pytest.mark.ui

OVERFLOW_SCRIPT = """() => {
  const width = document.documentElement.clientWidth;
  const offenders = [...document.querySelectorAll('body *')]
    .filter((el) => el.getBoundingClientRect().right > width + 1)
    .filter((el) => getComputedStyle(el).position !== 'fixed')
    .slice(0, 5)
    .map((el) => `${el.tagName.toLowerCase()}.${[...el.classList].slice(0, 3).join('.')}`);
  return { scrollWidth: document.documentElement.scrollWidth, width, offenders };
}"""


@pytest.mark.parametrize("width", MOBILE_WIDTHS, ids=lambda w: f"{w}px")
@pytest.mark.parametrize("path", KEY_PAGES)
def test_no_horizontal_scroll_on_phones(page: Page, path: str, width: int) -> None:
    page.set_viewport_size({"width": width, "height": 800})
    page.goto(path, wait_until="networkidle")
    result = page.evaluate(OVERFLOW_SCRIPT)
    assert result["scrollWidth"] <= result["width"], (
        f"page is {result['scrollWidth']}px wide on a {result['width']}px screen; "
        f"elements past the edge: {result['offenders']}"
    )


@pytest.mark.parametrize("path", KEY_PAGES)
def test_loads_without_errors(page: Page, console_errors: list[str], path: str) -> None:
    failed: list[str] = []

    def on_finished(request: Request) -> None:
        response = request.response()
        if response is not None and response.status >= 400:
            failed.append(f"{response.status} {request.url}")

    page.on("requestfinished", on_finished)
    page.on("requestfailed", lambda request: failed.append(f"failed {request.url}"))
    response = page.goto(path, wait_until="networkidle")
    assert response is not None
    assert response.status == 200
    assert failed == [], "requests that failed"
    assert console_errors == [], "errors in the browser console"
