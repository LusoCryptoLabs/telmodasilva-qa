"""What the suite knows about the site under test."""

import re
from functools import cache
from urllib.parse import urlsplit

import httpx

USER_AGENT = "telmodasilva-qa (+https://github.com/LusoCryptoLabs/telmodasilva-qa)"

# A short list of pages that stand for each template, so browser checks stay fast.
KEY_PAGES = [
    "/",
    "/biblioteca",
    "/sobre",
    "/curriculo",
    "/biblioteca/fundamentos-de-automacao-com-python",
    "/biblioteca/entrevistas-de-emprego",
    "/en",
    "/en/curriculo",
]

MOBILE_WIDTHS = [320, 360, 390, 414]


@cache
def sitemap_paths(base_url: str) -> tuple[str, ...]:
    """Paths listed in the live sitemap, rebased so the suite can run against any host."""
    response = httpx.get(f"{base_url}/sitemap.xml", headers={"user-agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    locations = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", response.text)
    return tuple(urlsplit(loc).path or "/" for loc in locations)


def locale_of(path: str) -> str:
    return "en" if path == "/en" or path.startswith("/en/") else "pt"
