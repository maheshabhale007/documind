from pathlib import Path

import chardet

from app.extractors.base import BaseExtractor


class TxtExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> list[tuple[int, str]]:
        raw = file_path.read_bytes()
        detected = chardet.detect(raw)
        encoding = detected.get("encoding") or "utf-8"
        text = raw.decode(encoding, errors="replace")
        return [(0, text)] if text.strip() else []
