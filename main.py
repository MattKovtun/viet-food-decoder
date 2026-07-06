"""CLI for the viet-food-decoder data pipeline.

Usage (inside .venv):
    python main.py fetch         # pull Wikipedia lists -> data/wikipedia.raw.json
    python main.py merge         # fill images, emit data/candidates.review.json
    python main.py find-images   # Commons search for dishes without img; fill img
    python main.py cache-images  # download Commons images -> img/, fill img_local
    python main.py gen-audio     # generate pronunciation MP3s -> audio/, fill audio
    python main.py validate      # schema-check data/dishes.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.audio_generator import AudioGenerator
from src.image_cacher import ImageCacher
from src.image_finder import ImageFinder
from src.merger import DatasetMerger
from src.models import Dish
from src.wikipedia_fetcher import WikipediaFetcher


class Pipeline:
    ROOT = Path(__file__).parent
    DISHES = ROOT / "data" / "dishes.json"
    RAW = ROOT / "data" / "wikipedia.raw.json"
    CANDIDATES = ROOT / "data" / "candidates.review.json"
    IMG_DIR = ROOT / "img"
    AUDIO_DIR = ROOT / "audio"

    def fetch(self) -> int:
        fetcher = WikipediaFetcher()
        entries = fetcher.fetch_all()
        self.RAW.write_text(
            json.dumps(
                {"attribution": WikipediaFetcher.ATTRIBUTION,
                 "entries": [e.to_dict() for e in entries]},
                ensure_ascii=False, indent=1,
            ),
            "utf-8",
        )
        print(f"wrote {len(entries)} raw entries -> {self.RAW}")
        return 0

    def merge(self) -> int:
        report = DatasetMerger(self.DISHES, self.RAW, self.CANDIDATES).run()
        print(report.summary())
        print(f"review new-dish candidates in {self.CANDIDATES}")
        return 0

    def cache_images(self) -> int:
        report = ImageCacher(self.DISHES, self.IMG_DIR).run()
        print(report.summary())
        return 1 if report.failed else 0

    def find_images(self) -> int:
        report = ImageFinder(self.DISHES).run()
        print(report.summary())
        print("review the picks above, then run cache-images")
        return 0

    def gen_audio(self) -> int:
        report = AudioGenerator(self.DISHES, self.AUDIO_DIR).run()
        print(report.summary())
        return 1 if report.failed else 0

    def validate(self) -> int:
        doc = json.loads(self.DISHES.read_text("utf-8"))
        problems: list[str] = []
        seen_ids: set[str] = set()
        for raw in doc["dishes"]:
            dish = Dish(**raw)
            problems.extend(dish.validate())
            if dish.id in seen_ids:
                problems.append(f"duplicate id: {dish.id}")
            seen_ids.add(dish.id)
            if dish.img_local and not (self.ROOT / dish.img_local).is_file():
                problems.append(f"{dish.id}: img_local missing on disk: {dish.img_local}")
            for clip in (dish.audio, dish.audio_m):
                if clip and not (self.ROOT / clip).is_file():
                    problems.append(f"{dish.id}: audio missing on disk: {clip}")
        if problems:
            print("\n".join(problems))
            return 1
        print(f"OK: {len(seen_ids)} dishes valid")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["fetch", "merge", "find-images", "cache-images", "gen-audio", "validate"])
    args = parser.parse_args()
    return getattr(Pipeline(), args.command.replace("-", "_"))()


if __name__ == "__main__":
    sys.exit(main())
