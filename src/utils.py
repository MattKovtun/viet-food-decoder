"""Pure text helpers (no configuration required)."""

from __future__ import annotations

import re
import unicodedata


class TextNormalizer:
    """Diacritic-insensitive normalization so 'Mì Quảng' == 'mi quang' == 'My Quang'-ish."""

    _WS = re.compile(r"\s+")
    _NON_ALNUM = re.compile(r"[^a-z0-9 ]+")

    # Vietnamese đ/Đ do not decompose via NFD; map explicitly.
    _DJ = str.maketrans({"đ": "d", "Đ": "d"})

    @classmethod
    def normalize(cls, text: str) -> str:
        """Lowercase, strip diacritics and punctuation, collapse whitespace."""
        text = text.translate(cls._DJ)
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        text = cls._NON_ALNUM.sub(" ", text.lower())
        return cls._WS.sub(" ", text).strip()

    @classmethod
    def slug(cls, text: str) -> str:
        return cls.normalize(text).replace(" ", "-")
