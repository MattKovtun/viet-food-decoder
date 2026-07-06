"""Data models for the Vietnamese food decoder dataset."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


class Taxonomy:
    """Canonical enums shared by the dataset and the UI. Keep in sync with data/schema.md."""

    PART_KINDS = {"base", "protein", "method", "place", "form", "plain"}

    CATEGORIES = {
        "noodle-soup", "noodle-dry", "rice", "roll", "cake",
        "main", "snack", "sweet", "drink",
    }

    FORMS = {"broth", "semi-dry", "dry", "roll", "rice", "cake", "snack", "sweet", "drink", "hotpot"}

    INGREDIENTS = {
        # bases
        "rice-noodle", "wheat-noodle", "glass-noodle", "tapioca-noodle", "rice",
        "broken-rice", "sticky-rice", "rice-paper", "rice-cracker", "baguette",
        # proteins
        "pork", "beef", "veal", "chicken", "duck", "fish", "fish-cake", "shrimp",
        "crab", "clam", "snail", "squid", "frog", "eel", "offal", "blood", "balut",
        "egg", "quail-egg", "tofu",
        # plants & extras
        "jackfruit", "papaya", "green-banana", "banana", "corn", "avocado",
        "mung-bean", "peanut", "sesame", "coconut", "herbs", "lemongrass",
        "turmeric", "ginger", "dill", "chili", "tomato", "pineapple",
        "carrot", "bamboo-shoot", "tamarind", "bitter-melon", "yam", "soybean",
        "plum", "durian", "lotus-seed", "longan", "birds-nest", "cassava",
        "peach", "artichoke",
        # dairy/sweet/drink
        "condensed-milk", "yogurt", "coffee", "tea", "sugarcane", "jelly",
        # sauces that define the dish (used for exclude-filters)
        "fish-sauce", "fermented-fish", "shrimp-paste", "pate",
    }


@dataclass
class Dish:
    """One curated dish entry."""

    id: str
    name: str
    parts: list[list[str]]           # [["mì","base"],["Quảng","place"]]
    pron: str
    lit: str
    desc: str
    region: str
    central: bool                    # Da Nang / central-Vietnam specialty
    cat: str                         # Taxonomy.CATEGORIES
    form: str                        # Taxonomy.FORMS
    ingredients: list[str]           # Taxonomy.INGREDIENTS
    spice: int                       # 0..3, heat level AS SERVED (other axes archived 2026-07-05:
                                     # data/flavor.archive.json — too stall-dependent to be useful)
    spice_varies: bool = False       # heat depends heavily on the stall (bánh mì chili spread etc.)
    aka: list[str] = field(default_factory=list)  # pure synonyms (same bowl, other name), searchable
    variants: list[dict[str, str]] = field(default_factory=list)
    # order-variants that change what arrives: [{"name": "bún giò", "note": "pork knuckle …"}]
    history: str = ""                # origin story + cultural impact; collapsed section in the UI
    img: str | None = None           # Wikimedia Commons URL when known
    img_verified: bool = False       # True = image came from the curated Wikipedia-list match,
                                     # not from Commons keyword search (the ★ on the site)
    img_query: str = ""              # fallback image-search query
    img_local: str | None = None     # repo-relative cached copy (img/<id>.<ext>), set by cache-images
    audio: str | None = None         # pronunciation clip, female voice (audio/<id>.mp3), set by gen-audio
    audio_m: str | None = None       # pronunciation clip, deep male voice (audio/<id>-m.mp3), set by gen-audio
    srcs: list[str] = field(default_factory=lambda: ["handbook"])

    def validate(self) -> list[str]:
        """Return a list of human-readable problems; empty list means valid."""
        problems: list[str] = []
        if self.cat not in Taxonomy.CATEGORIES:
            problems.append(f"{self.id}: unknown cat '{self.cat}'")
        if self.form not in Taxonomy.FORMS:
            problems.append(f"{self.id}: unknown form '{self.form}'")
        for kind in {p[1] for p in self.parts}:
            if kind not in Taxonomy.PART_KINDS:
                problems.append(f"{self.id}: unknown part kind '{kind}'")
        for ing in self.ingredients:
            if ing not in Taxonomy.INGREDIENTS:
                problems.append(f"{self.id}: unknown ingredient '{ing}'")
        if not all(isinstance(a, str) and a for a in self.aka):
            problems.append(f"{self.id}: aka must be non-empty strings")
        for v in self.variants:
            keys = set(v)
            if not {"name", "note"} <= keys <= {"name", "note", "spice"}:
                problems.append(f"{self.id}: variant needs 'name'+'note' (optional 'spice'): {v!r}")
            elif not all(isinstance(v[k], str) and v[k] for k in ("name", "note")):
                problems.append(f"{self.id}: variant name/note must be non-empty strings: {v!r}")
            elif "spice" in v and (not isinstance(v["spice"], int) or not 0 <= v["spice"] <= 3):
                problems.append(f"{self.id}: variant spice must be int 0..3: {v!r}")
        if not isinstance(self.spice, int) or not 0 <= self.spice <= 3:
            problems.append(f"{self.id}: spice must be int 0..3, got {self.spice!r}")
        if self.img_verified and not (self.img or self.img_local):
            problems.append(f"{self.id}: img_verified without any image")
        return problems

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RawWikiEntry:
    """One row extracted from a Wikipedia list page (facts + CC-BY-SA description seed)."""

    name: str
    desc: str
    region: str
    img: str | None
    source_page: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
