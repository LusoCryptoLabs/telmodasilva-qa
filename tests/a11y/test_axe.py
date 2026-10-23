"""Automated accessibility scan (WCAG 2.1 A and AA rules) with axe-core.

Known violations are listed with the reason they are still open. A page that only has
known violations is reported as xfail; any other serious or critical violation fails.
"""

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page

from qa.site import KEY_PAGES

pytestmark = pytest.mark.a11y

BLOCKING_IMPACTS = {"critical", "serious"}
WCAG_AA = {"runOnly": {"type": "tag", "values": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]}}

KNOWN = {
    "color-contrast": "the light suffix in the logo is below 4.5:1",
    "link-in-text-block": "links inside paragraphs are told apart by colour only",
    "label": "the code editor of the graded challenge has no accessible name",
}


@pytest.fixture(scope="session")
def axe() -> Axe:
    return Axe()


def describe(violation: dict) -> str:
    targets = [", ".join(node["target"]) for node in violation["nodes"][:3]]
    return f"{violation['id']} ({violation['impact']}): {violation['help']} at {targets}"


@pytest.mark.parametrize("path", KEY_PAGES)
def test_no_serious_violations(page: Page, axe: Axe, path: str) -> None:
    page.goto(path, wait_until="networkidle")
    results = axe.run(page, options=WCAG_AA)
    blocking = [v for v in results.response["violations"] if v["impact"] in BLOCKING_IMPACTS]

    new = [v for v in blocking if v["id"] not in KNOWN]
    assert new == [], "\n".join(describe(v) for v in new)

    known = sorted({v["id"] for v in blocking})
    if known:
        pytest.xfail("known: " + "; ".join(f"{rule} ({KNOWN[rule]})" for rule in known))
