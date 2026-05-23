from abc import ABC, abstractmethod
from pathlib import Path


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: Path) -> list[tuple[int, str]]:
        """
        Extract text from a file.
        Returns a list of (page_number, page_text) tuples.
        For files without pages (TXT, DOCX), returns [(0, full_text)].
        """
        ...


def get_extractor(file_extension: str) -> "BaseExtractor":
    from app.extractors.pdf_extractor import PdfExtractor
    from app.extractors.docx_extractor import DocxExtractor
    from app.extractors.txt_extractor import TxtExtractor

    ext = file_extension.lower().lstrip(".")
    mapping = {
        "pdf": PdfExtractor,
        "docx": DocxExtractor,
        "doc": DocxExtractor,
        "txt": TxtExtractor,
        "md": TxtExtractor,
    }
    cls = mapping.get(ext)
    if cls is None:
        raise ValueError(f"Unsupported file type: .{ext}")
    return cls()
