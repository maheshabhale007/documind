from pathlib import Path

import fitz  # PyMuPDF

from app.extractors.base import BaseExtractor


class PdfExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> list[tuple[int, str]]:
        pages = []
        with fitz.open(str(file_path)) as doc:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                if text.strip():
                    pages.append((page_num, text))
        return pages
