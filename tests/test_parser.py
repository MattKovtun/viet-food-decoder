"""Fixture test for WikipediaFetcher.parse_page (run: .venv/bin/python -m tests.test_parser)."""

from __future__ import annotations

from src.utils import TextNormalizer
from src.wikipedia_fetcher import WikipediaFetcher


class ParserTest:
    FIXTURE = """
    <h2>Noodle dishes<span>[edit]</span></h2>
    <table class="wikitable">
      <tr><th>Name</th><th>Image</th><th>Description</th></tr>
      <tr>
        <td><a href="/wiki/M%C3%AC_Qu%E1%BA%A3ng">Mì Quảng</a></td>
        <td><img src="//upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Mi_Quang.jpg/120px-Mi_Quang.jpg"></td>
        <td>Turmeric rice noodles from Quảng Nam served with pork and shrimp.</td>
      </tr>
      <tr>
        <td>Bún bò Huế</td>
        <td></td>
        <td>Spicy lemongrass beef noodle soup from Huế.</td>
      </tr>
    </table>
    """

    def run(self) -> None:
        fetcher = WikipediaFetcher()
        entries = fetcher.parse_page(self.FIXTURE, "List of Vietnamese dishes")

        assert len(entries) == 2, f"expected 2 entries, got {len(entries)}"
        first, second = entries

        assert first.name == "Mì Quảng"
        assert first.region == "Noodle dishes"
        assert first.img == "https://upload.wikimedia.org/wikipedia/commons/a/ab/Mi_Quang.jpg", first.img
        assert "Quảng Nam" in first.desc

        assert second.img is None
        assert TextNormalizer.normalize(second.name) == "bun bo hue"

        print("parser fixture test: OK")


if __name__ == "__main__":
    ParserTest().run()
