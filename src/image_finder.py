"""Find Commons images for dishes that have none, via the official Commons search API.

Deliberately NOT Google Images: random web results are copyrighted, and the
project rule is Commons-only images (licensed, hotlink-safe). Commons search
ranks by relevance; we take the best bitmap hit of usable size and fill `img`
(the original file URL). `cache-images` then downloads it as usual.

Search hits can be the wrong dish entirely (a plain "mit tron" query returns
Audi e-tron photos), so hits are ranked in two tiers:
- exact: the normalized file title contains every token of the dish name
- loose: best bitmap hit for the query, flagged REVIEW in the report
Every pick must be eyeballed before committing; loose ones especially.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from src.utils import TextNormalizer


@dataclass
class FindReport:
    exact: int
    loose: int
    skipped_has_img: int
    no_hit: list[str]

    def summary(self) -> str:
        line = (f"exact={self.exact} loose(REVIEW)={self.loose} "
                f"already_had={self.skipped_has_img} no_hit={len(self.no_hit)}")
        if self.no_hit:
            line += "\n" + "\n".join(f"  NO HIT {d}" for d in self.no_hit)
        return line


class ImageFinder:
    # Commons has no usable photo for these (verified by hand, repeatedly — the search
    # returns Audi e-trons and massage diagrams). Skip them; they await own-photos.
    NO_COMMONS = {"mit-tron", "com-ga-hoi-an", "banh-dap", "oc-hut",
                  "che-xoa-xoa", "tau-hu", "kem-bo"}

    API_URL = "https://commons.wikimedia.org/w/api.php"
    USER_AGENT = os.getenv(
        "WIKI_USER_AGENT",
        "viet-food-decoder/0.1 (personal research)",
    )
    MIN_WIDTH = 400
    MIMES = {"image/jpeg", "image/png"}
    DELAY_S = 1.5   # between every API request — Commons 429s bursts
    RETRIES = 4

    def __init__(self, dishes_path: Path, session: requests.Session | None = None) -> None:
        self._dishes_path = dishes_path
        self._session = session or requests.Session()
        self._session.headers["User-Agent"] = self.USER_AGENT

    def run(self) -> FindReport:
        doc = json.loads(self._dishes_path.read_text("utf-8"))
        dishes: list[dict[str, Any]] = doc["dishes"]

        exact, loose, had, no_hit = 0, 0, 0, []
        for dish in dishes:
            if dish.get("img") or dish.get("img_local") or dish["id"] in self.NO_COMMONS:
                had += 1
                continue
            found = self._find(dish)
            if found is None:
                no_hit.append(dish["id"])
                continue
            title, url, mode = found
            dish["img"] = url
            if "wikipedia" not in dish["srcs"]:
                dish["srcs"].append("wikipedia")
            if mode == "exact":
                exact += 1
                print(f"  {dish['id']}: {title}")
            else:
                loose += 1
                print(f"  {dish['id']}: {title}   << REVIEW (loose match)")

        self._dishes_path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=1), "utf-8"
        )
        return FindReport(exact, loose, had, no_hit)

    def _find(self, dish: dict[str, Any]) -> tuple[str, str, str] | None:
        name = dish["name"].split("/")[0].strip()
        queries = [q for q in (name, dish.get("img_query", "")) if q]
        tokens = [t for t in TextNormalizer.normalize(name).split() if len(t) >= 2]

        hits_per_query = [self._hits(q) for q in queries]
        for hits in hits_per_query:
            for title, url in hits:
                title_norm = TextNormalizer.normalize(title)
                if tokens and all(t in title_norm for t in tokens):
                    return title, url, "exact"
        for hits in hits_per_query:
            if hits:
                return (*hits[0], "loose")
        return None

    def _hits(self, query: str) -> list[tuple[str, str]]:
        """Bitmap hits (title, original URL) for a Commons file search, relevance order."""
        for attempt in range(self.RETRIES):
            resp = self._session.get(self.API_URL, params={
                "action": "query", "format": "json",
                "generator": "search", "gsrsearch": query,
                "gsrnamespace": 6, "gsrlimit": 8,
                "prop": "imageinfo", "iiprop": "url|size|mime",
            }, timeout=30)
            time.sleep(self.DELAY_S)
            if resp.status_code == 429:
                time.sleep(15.0 * (attempt + 1))
                continue
            resp.raise_for_status()
            break
        else:
            raise RuntimeError(f"Commons API kept rate-limiting for query: {query}")

        pages = resp.json().get("query", {}).get("pages", {})
        ranked = sorted(pages.values(), key=lambda p: p.get("index", 999))
        return [
            (p["title"], info["url"])
            for p in ranked
            if (info := (p.get("imageinfo") or [{}])[0]).get("mime") in self.MIMES
            and info.get("width", 0) >= self.MIN_WIDTH
        ]
