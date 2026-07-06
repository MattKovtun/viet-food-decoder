"""Download each dish's Commons image into img/ and record it as img_local.

Rules:
- Fetch the 960px thumb (a width Wikimedia serves to anonymous clients, see
  https://w.wiki/GHai); fall back to the original file if the thumb errors.
- Files land in img/<dish-id>.<ext>; dishes.json gets `img_local` filled in.
- Existing files are kept (delete a file to force a re-download).
- `img` stays the Commons original URL — it is the provenance/attribution link.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


@dataclass
class CacheReport:
    downloaded: int
    kept: int
    failed: list[str]

    def summary(self) -> str:
        line = f"downloaded={self.downloaded} kept={self.kept} failed={len(self.failed)}"
        if self.failed:
            line += "\n" + "\n".join(f"  FAILED {f}" for f in self.failed)
        return line


class ImageCacher:
    USER_AGENT = os.getenv(
        "WIKI_USER_AGENT",
        "viet-food-decoder/0.1 (personal research)",
    )
    THUMB_WIDTH = 960  # must be one of Wikimedia's fixed anonymous widths
    DELAY_S = 1.0      # be polite; Wikimedia 429s unauthenticated bursts
    RETRIES = 3

    _COMMONS = re.compile(
        r"^(https://upload\.wikimedia\.org/wikipedia/commons)/([0-9a-f])/([0-9a-f]{2})/([^/]+)$"
    )

    def __init__(self, dishes_path: Path, img_dir: Path,
                 session: requests.Session | None = None) -> None:
        self._dishes_path = dishes_path
        self._img_dir = img_dir
        self._session = session or requests.Session()
        self._session.headers["User-Agent"] = self.USER_AGENT

    def run(self) -> CacheReport:
        doc = json.loads(self._dishes_path.read_text("utf-8"))
        dishes: list[dict[str, Any]] = doc["dishes"]
        self._img_dir.mkdir(exist_ok=True)

        downloaded, kept, failed = 0, 0, []
        for dish in dishes:
            url = dish.get("img")
            if not url:
                # adopt owner-dropped photos: img/<id>.<ext> with no image record yet
                if not dish.get("img_local"):
                    for ext in (".jpg", ".jpeg", ".png", ".webp"):
                        orphan = self._img_dir / f"{dish['id']}{ext}"
                        if orphan.is_file():
                            dish["img_local"] = f"{self._img_dir.name}/{orphan.name}"
                            dish["img_verified"] = True
                            if "own-photo" not in dish["srcs"]:
                                dish["srcs"].append("own-photo")
                            kept += 1
                            print(f"  adopted own photo: {dish['img_local']}")
                            break
                continue
            dest = self._img_dir / f"{dish['id']}{self._ext(url)}"
            rel = f"{self._img_dir.name}/{dest.name}"
            if dest.exists():
                kept += 1
                dish["img_local"] = rel
                continue
            data = self._download(url)
            if data is None:
                failed.append(f"{dish['id']}: {url}")
                continue
            dest.write_bytes(data)
            dish["img_local"] = rel
            downloaded += 1
            print(f"  {rel} ({len(data) // 1024} KB)")
            time.sleep(self.DELAY_S)

        self._dishes_path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=1), "utf-8"
        )
        return CacheReport(downloaded, kept, failed)

    def _download(self, url: str) -> bytes | None:
        """Try the 960px thumb, then the original; retry 429/5xx with backoff."""
        for candidate in (self._thumb_url(url), url):
            if candidate is None:
                continue
            for attempt in range(self.RETRIES):
                resp = self._session.get(candidate, timeout=30)
                if resp.status_code == 200:
                    return resp.content
                if resp.status_code == 429 or resp.status_code >= 500:
                    time.sleep(2.0 * (attempt + 1))
                    continue
                break  # 4xx other than 429: try next candidate
        return None

    @classmethod
    def _thumb_url(cls, url: str) -> str | None:
        m = cls._COMMONS.match(url)
        if not m:
            return None
        host, d1, d2, name = m.groups()
        return f"{host}/thumb/{d1}/{d2}/{name}/{cls.THUMB_WIDTH}px-{name}"

    @staticmethod
    def _ext(url: str) -> str:
        suffix = Path(url).suffix.lower()
        return suffix if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp"} else ".jpg"
