"""Merge raw Wikipedia entries into the curated dataset.

Rules:
- Match by diacritic-insensitive name (raw name may contain the curated name or vice versa).
- Matched: fill `img` if missing, append 'wikipedia' to srcs.
- Unmatched raw entries become stub candidates in a separate review file
  (never auto-added to dishes.json — curation stays deliberate).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.models import RawWikiEntry
from src.utils import TextNormalizer


@dataclass
class MergeReport:
    matched: int
    images_filled: int
    candidates: int

    def summary(self) -> str:
        return (
            f"matched={self.matched} images_filled={self.images_filled} "
            f"new_candidates={self.candidates}"
        )


class DatasetMerger:
    def __init__(self, dishes_path: Path, raw_path: Path, candidates_path: Path) -> None:
        self._dishes_path = dishes_path
        self._raw_path = raw_path
        self._candidates_path = candidates_path

    def run(self) -> MergeReport:
        dishes: list[dict[str, Any]] = json.loads(self._dishes_path.read_text("utf-8"))["dishes"]
        raw_doc = json.loads(self._raw_path.read_text("utf-8"))
        raw = [RawWikiEntry(**e) for e in raw_doc["entries"]]

        index = {TextNormalizer.normalize(d["name"]): d for d in dishes}
        matched = images_filled = 0
        candidates: list[dict[str, Any]] = []

        for entry in raw:
            key = TextNormalizer.normalize(entry.name)
            dish = index.get(key) or self._fuzzy(index, key)
            if dish is not None:
                matched += 1
                if not dish.get("img") and entry.img:
                    dish["img"] = entry.img
                    images_filled += 1
                if "wikipedia" not in dish["srcs"]:
                    dish["srcs"].append("wikipedia")
            else:
                candidates.append(entry.to_dict())

        doc = {"dishes": dishes}
        self._dishes_path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=1), "utf-8"
        )
        self._candidates_path.write_text(
            json.dumps({"attribution": raw_doc.get("attribution", ""), "candidates": candidates},
                       ensure_ascii=False, indent=1),
            "utf-8",
        )
        return MergeReport(matched, images_filled, len(candidates))

    @staticmethod
    def _fuzzy(index: dict[str, dict[str, Any]], key: str) -> dict[str, Any] | None:
        """Containment match: 'banh xeo mien trung' should hit 'banh xeo'."""
        for dish_key, dish in index.items():
            if dish_key and (dish_key in key or key in dish_key):
                return dish
        return None
