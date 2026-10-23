"""Search and sharing metadata for every page in the sitemap."""

from urllib.parse import urlsplit

import httpx
import pytest

from qa.html_head import Head, parse_head
from qa.site import CANONICAL_ORIGIN, locale_of, sitemap_paths

pytestmark = pytest.mark.content


@pytest.fixture(scope="module")
def heads(http: httpx.Client, site: str) -> dict[str, Head]:
    return {path: parse_head(http.get(path).text) for path in sitemap_paths(site)}


def test_title(heads: dict[str, Head], sitemap_path: str) -> None:
    head = heads[sitemap_path]
    assert len(head.titles) == 1, f"expected one <title> in <head>, found {head.titles}"
    assert "Telmo da Silva" in head.titles[0]


def test_description(heads: dict[str, Head], sitemap_path: str) -> None:
    description = heads[sitemap_path].description
    assert description, "missing meta description"
    assert len(description) >= 50, f"only {len(description)} characters"


def test_canonical_points_to_itself(heads: dict[str, Head], sitemap_path: str) -> None:
    canonical = heads[sitemap_path].canonical
    assert canonical, "missing canonical link"
    assert canonical.rstrip("/") == f"{CANONICAL_ORIGIN}{sitemap_path}".rstrip("/")


def test_one_h1(heads: dict[str, Head], sitemap_path: str) -> None:
    assert heads[sitemap_path].h1_count == 1


def test_indexable(heads: dict[str, Head], sitemap_path: str) -> None:
    # A page in the sitemap that asks not to be indexed sends crawlers mixed signals.
    assert "noindex" not in (heads[sitemap_path].robots or "")


def test_html_lang_matches_locale(heads: dict[str, Head], sitemap_path: str) -> None:
    assert heads[sitemap_path].lang == locale_of(sitemap_path)


def test_share_image(heads: dict[str, Head], http: httpx.Client, sitemap_path: str) -> None:
    image = heads[sitemap_path].og_image
    assert image, "missing og:image"
    # Fetch it from the environment under test, not from the origin baked into the URL.
    parts = urlsplit(image)
    response = http.get(f"{parts.path}?{parts.query}" if parts.query else parts.path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")


@pytest.mark.parametrize("field", ["title", "description"])
def test_unique_across_pages(heads: dict[str, Head], field: str) -> None:
    seen: dict[str, str] = {}
    for path, head in heads.items():
        value = (head.titles[:1] or [""])[0] if field == "title" else head.description or ""
        assert value not in seen, f"{path} repeats the {field} of {seen[value]}"
        seen[value] = path
