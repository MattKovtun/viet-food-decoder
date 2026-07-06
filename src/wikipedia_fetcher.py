"""Fetch and parse Wikipedia's Vietnamese-dish list pages into raw JSON.

Content source: English Wikipedia (CC BY-SA 4.0). We extract facts (names, regions)
plus short description seeds and Commons image URLs. Attribution is emitted into the
output file so the final site footer can cite it.
"""

from __future__ import annotations

import os

import requests
from bs4 import BeautifulSoup, Tag

from src.models import RawWikiEntry


class WikipediaFetcher:
    """Pulls rendered HTML for list pages via the MediaWiki API and parses wikitables."""

    # .env can override (WIKI_API_URL=...); sensible default otherwise.
    API_URL = os.getenv("WIKI_API_URL", "https://en.wikipedia.org/w/api.php")
    USER_AGENT = os.getenv(
        "WIKI_USER_AGENT",
        "viet-food-decoder/0.1 (personal research; contact via github)",
    )
    PAGES = (
        "List of Vietnamese dishes",
        "List of Vietnamese culinary specialities",
    )
    ATTRIBUTION = (
        "Contains material derived from Wikipedia, licensed CC BY-SA 4.0: "
        "https://en.wikipedia.org/wiki/List_of_Vietnamese_dishes and "
        "https://en.wikipedia.org/wiki/List_of_Vietnamese_culinary_specialities"
    )

    def __init__(self, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()
        self._session.headers["User-Agent"] = self.USER_AGENT

    # ------------------------------------------------------------------ fetch

    def fetch_page_html(self, page_title: str) -> str:
        """Return rendered HTML of a wiki page via action=parse."""
        resp = self._session.get(
            self.API_URL,
            params={
                "action": "parse",
                "page": page_title,
                "prop": "text",
                "format": "json",
                "formatversion": "2",
                "redirects": "1",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["parse"]["text"]

    def fetch_all(self) -> list[RawWikiEntry]:
        entries: list[RawWikiEntry] = []
        for page in self.PAGES:
            entries.extend(self.parse_page(self.fetch_page_html(page), page))
        return entries

    # ------------------------------------------------------------------ parse

    def parse_page(self, html: str, source_page: str) -> list[RawWikiEntry]:
        """Parse every wikitable; nearest preceding h2/h3 heading becomes the region/section."""
        soup = BeautifulSoup(html, "html.parser")
        entries: list[RawWikiEntry] = []
        for table in soup.select("table.wikitable"):
            region = self._nearest_heading(table)
            entries.extend(self._parse_table(table, region, source_page))
        return entries

    def _nearest_heading(self, table: Tag) -> str:
        for prev in table.find_all_previous(["h2", "h3"]):
            text = prev.get_text(" ", strip=True)
            text = text.replace("[edit]", "").strip()
            if text and text.lower() not in {"contents", "see also", "references"}:
                return text
        return ""

    def _parse_table(self, table: Tag, region: str, source_page: str) -> list[RawWikiEntry]:
        entries: list[RawWikiEntry] = []
        for row in table.select("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2 or row.find("th") and row.find_all("th") == cells:
                continue  # header row or malformed
            name = cells[0].get_text(" ", strip=True)
            if not name or name.lower() in {"name", "dish"}:
                continue
            desc = self._description_cell(cells)
            img = self._image_url(row)
            entries.append(
                RawWikiEntry(name=name, desc=desc, region=region, img=img, source_page=source_page)
            )
        return entries

    def _description_cell(self, cells: list[Tag]) -> str:
        # Longest non-name cell text is the description in both list layouts.
        texts = [c.get_text(" ", strip=True) for c in cells[1:]]
        return max(texts, key=len, default="")

    def _image_url(self, row: Tag) -> str | None:
        img = row.find("img")
        if img is None or not img.get("src"):
            return None
        src: str = img["src"]
        if src.startswith("//"):
            src = "https:" + src
        # Upgrade thumbnail to original: .../thumb/a/ab/File.jpg/120px-File.jpg -> .../a/ab/File.jpg
        if "/thumb/" in src:
            base, _, _ = src.rpartition("/")
            src = base.replace("/thumb/", "/", 1)
        return src
