from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from playwright.sync_api import BrowserContext, ConsoleMessage, Page, Route

from qa.site import CANONICAL_ORIGIN, USER_AGENT, sitemap_paths


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "sitemap_path" in metafunc.fixturenames:
        config = metafunc.config
        base_url = config.getoption("base_url") or config.getini("base_url")
        paths = sitemap_paths(base_url.rstrip("/"))
        metafunc.parametrize("sitemap_path", paths, ids=list(paths))


@pytest.fixture(scope="session")
def site(base_url: str) -> str:
    return base_url.rstrip("/")


@pytest.fixture
def production_only(site: str) -> None:
    """Redirects and security headers live in the production proxy, not in the app."""
    if site != CANONICAL_ORIGIN:
        pytest.skip("production proxy behaviour")


@pytest.fixture(scope="session")
def http(site: str) -> Iterator[httpx.Client]:
    with httpx.Client(
        base_url=site, headers={"user-agent": USER_AGENT}, timeout=30, follow_redirects=False
    ) as client:
        yield client


@pytest.fixture
def analytics_events() -> list[dict[str, Any]]:
    """Every analytics call the page tried to make. None of them reach the server."""
    return []


@pytest.fixture
def context(context: BrowserContext, analytics_events: list[dict[str, Any]]) -> BrowserContext:
    # Test runs must not count as visits on the live site.
    def stub(route: Route) -> None:
        analytics_events.append(route.request.post_data_json or {})
        route.fulfill(status=200, json={"ok": True})

    context.route("**/api/analytics", stub)
    return context


@pytest.fixture
def console_errors(page: Page) -> list[str]:
    errors: list[str] = []

    def on_console(message: ConsoleMessage) -> None:
        if message.type == "error":
            errors.append(message.text)

    page.on("console", on_console)
    page.on("pageerror", lambda exc: errors.append(f"uncaught: {exc}"))
    return errors
