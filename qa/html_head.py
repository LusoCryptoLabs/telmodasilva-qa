"""Reads the document head.

Inline SVGs in the body carry their own <title>, so only the one inside <head> counts.
"""

from dataclasses import dataclass, field
from html.parser import HTMLParser


@dataclass
class Head:
    lang: str | None = None
    titles: list[str] = field(default_factory=list)
    description: str | None = None
    canonical: str | None = None
    og_image: str | None = None
    robots: str | None = None
    h1_count: int = 0


class _HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.head = Head()
        self._in_head = False
        self._title: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "html":
            self.head.lang = a.get("lang")
        elif tag == "head":
            self._in_head = True
        elif tag == "h1":
            self.head.h1_count += 1
        elif self._in_head:
            if tag == "title":
                self._title = []
            elif tag == "meta":
                if a.get("name") == "description":
                    self.head.description = a.get("content")
                elif a.get("name") == "robots":
                    self.head.robots = a.get("content")
                elif a.get("property") == "og:image":
                    self.head.og_image = a.get("content")
            elif tag == "link" and a.get("rel") == "canonical":
                self.head.canonical = a.get("href")

    def handle_endtag(self, tag: str) -> None:
        if tag == "head":
            self._in_head = False
        elif tag == "title" and self._title is not None:
            self.head.titles.append("".join(self._title).strip())
            self._title = None

    def handle_data(self, data: str) -> None:
        if self._title is not None:
            self._title.append(data)


def parse_head(html: str) -> Head:
    parser = _HeadParser()
    parser.feed(html)
    return parser.head
