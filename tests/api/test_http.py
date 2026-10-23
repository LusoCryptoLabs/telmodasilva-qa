"""Transport-level behaviour: redirects, headers, status codes, crawler files."""

import httpx
import pytest

pytestmark = pytest.mark.api

SECURITY_HEADERS = {
    "strict-transport-security": "max-age=",
    "x-content-type-options": "nosniff",
    "x-frame-options": "SAMEORIGIN",
    "referrer-policy": "strict-origin-when-cross-origin",
}


def test_http_redirects_to_https(site: str) -> None:
    insecure = site.replace("https://", "http://", 1)
    response = httpx.get(f"{insecure}/sobre", follow_redirects=False, timeout=30)
    assert response.status_code == 301
    assert response.headers["location"] == f"{site}/sobre"


def test_www_redirects_to_apex_keeping_the_path(site: str) -> None:
    www = site.replace("https://", "https://www.", 1)
    response = httpx.get(f"{www}/sobre", follow_redirects=False, timeout=30)
    assert response.status_code == 301
    assert response.headers["location"] == f"{site}/sobre"


@pytest.mark.parametrize(("header", "expected"), SECURITY_HEADERS.items())
def test_security_header(http: httpx.Client, header: str, expected: str) -> None:
    assert expected in http.get("/").headers.get(header, "")


def test_unknown_page_returns_404(http: httpx.Client) -> None:
    assert http.get("/this-page-does-not-exist").status_code == 404


def test_robots_allows_crawling_and_points_to_the_sitemap(http: httpx.Client, site: str) -> None:
    robots = http.get("/robots.txt")
    assert robots.status_code == 200
    lines = [line.strip() for line in robots.text.splitlines()]
    assert "Disallow: /" not in lines
    assert f"Sitemap: {site}/sitemap.xml" in lines


def test_sitemap_lists_only_this_site(http: httpx.Client, site: str) -> None:
    sitemap = http.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "xml" in sitemap.headers["content-type"]
    locations = [part.split("</loc>")[0].strip() for part in sitemap.text.split("<loc>")[1:]]
    assert len(locations) >= 10
    assert all(loc.startswith(site) for loc in locations)
    assert len(locations) == len(set(locations)), "duplicate URLs in the sitemap"


def test_sitemap_page_is_served_directly(http: httpx.Client, sitemap_path: str) -> None:
    # A sitemap entry that redirects or fails wastes crawl budget and hides a broken link.
    assert http.get(sitemap_path).status_code == 200
