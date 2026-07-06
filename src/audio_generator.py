"""Generate a spoken-pronunciation clip per dish and record it as `audio`.

Uses Microsoft Edge neural TTS (edge-tts package) with a native Vietnamese
voice — generation is a one-time pipeline step; the site itself just serves
the committed MP3s, so there is no runtime dependency on the TTS service.

Rules mirror image_cacher: audio/<dish-id>.mp3, existing files are kept
(delete a file to force regeneration), dishes.json gets `audio` filled in.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import edge_tts


@dataclass
class AudioReport:
    generated: int
    kept: int
    failed: list[str]

    def summary(self) -> str:
        line = f"generated={self.generated} kept={self.kept} failed={len(self.failed)}"
        if self.failed:
            line += "\n" + "\n".join(f"  FAILED {f}" for f in self.failed)
        return line


class AudioGenerator:
    # (dish field, filename suffix, voice) — one clip per voice per dish
    VOICES = (
        ("audio", "", os.getenv("TTS_VOICE", "vi-VN-HoaiMyNeural")),
        ("audio_m", "-m", os.getenv("TTS_VOICE_M", "vi-VN-NamMinhNeural")),
    )
    DELAY_S = 0.5  # be polite to the TTS endpoint

    def __init__(self, dishes_path: Path, audio_dir: Path) -> None:
        self._dishes_path = dishes_path
        self._audio_dir = audio_dir

    def run(self) -> AudioReport:
        return asyncio.run(self._run())

    async def _run(self) -> AudioReport:
        doc = json.loads(self._dishes_path.read_text("utf-8"))
        dishes: list[dict[str, Any]] = doc["dishes"]
        self._audio_dir.mkdir(exist_ok=True)

        generated, kept, failed = 0, 0, []
        for dish in dishes:
            # speak the primary Vietnamese name only (strip alt spellings after '/')
            text = dish["name"].split("/")[0].strip()
            for field, suffix, voice in self.VOICES:
                dest = self._audio_dir / f"{dish['id']}{suffix}.mp3"
                rel = f"{self._audio_dir.name}/{dest.name}"
                if dest.exists() and dest.stat().st_size >= 1000:
                    kept += 1
                    dish[field] = rel
                    continue
                dest.unlink(missing_ok=True)  # 0-byte carcass from a failed stream
                try:
                    await edge_tts.Communicate(text, voice).save(str(dest))
                    if dest.stat().st_size < 1000:
                        raise RuntimeError("suspiciously small file")
                except Exception as exc:
                    dest.unlink(missing_ok=True)
                    failed.append(f"{dish['id']} [{voice}]: {exc}")
                    continue
                dish[field] = rel
                generated += 1
                print(f"  {rel} ({dest.stat().st_size // 1024} KB) ← “{text}”")
                await asyncio.sleep(self.DELAY_S)

        self._dishes_path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=1), "utf-8"
        )
        return AudioReport(generated, kept, failed)
