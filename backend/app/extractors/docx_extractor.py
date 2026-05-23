from pathlib import Path

from docx import Document

from app.extractors.base import BaseExtractor


class DocxExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> list[tuple[int, str]]:
        doc = Document(str(file_path))
        full_text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        return [(0, full_text)] if full_text else []
