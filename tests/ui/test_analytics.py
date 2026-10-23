"""The site's own first-party analytics, observed in the browser.

The suite stubs /api/analytics for every page (see conftest), so these checks see
exactly what a visitor's browser would send, and nothing reaches the server.
"""

import re
from typing import Any

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.ui


def views(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in events if event.get("ev") == "vista"]


def test_one_page_view_per_load(page: Page, analytics_events: list[dict[str, Any]]) -> None:
    page.goto("/sobre", wait_until="networkidle")
    sent = views(analytics_events)
    assert len(sent) == 1
    assert sent[0]["path"] == "/sobre"
    assert re.fullmatch(r"[A-Za-z0-9-]{1,64}", sent[0]["vid"]), "visitor id fails server rules"


def test_visitor_id_is_stable_across_pages(
    page: Page, analytics_events: list[dict[str, Any]]
) -> None:
    page.goto("/sobre", wait_until="networkidle")
    page.goto("/biblioteca", wait_until="networkidle")
    sent = views(analytics_events)
    assert [event["path"] for event in sent] == ["/sobre", "/biblioteca"]
    assert sent[0]["vid"] == sent[1]["vid"]


def test_owner_opt_out_stops_all_events(page: Page, analytics_events: list[dict[str, Any]]) -> None:
    page.goto("/sobre?nao-contar", wait_until="networkidle")
    page.goto("/biblioteca", wait_until="networkidle")
    assert analytics_events == []
