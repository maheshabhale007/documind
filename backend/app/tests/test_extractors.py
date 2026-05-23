import tempfile
from pathlib import Path

import pytest

from app.extractors.txt_extractor import TxtExtractor
from app.extractors.base import get_extractor


def test_txt_extractor_utf8():
    extractor = TxtExtractor()
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as f:
        f.write("Hello world. This is a test document.".encode("utf-8"))
        path = Path(f.name)

    pages = extractor.extract(path)
    path.unlink()

    assert len(pages) == 1
    assert pages[0][0] == 0  # page number
    assert "Hello world" in pages[0][1]


def test_txt_extractor_latin1():
    extractor = TxtExtractor()
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as f:
        f.write("Caf\xe9 au lait".encode("latin-1"))
        path = Path(f.name)

    pages = extractor.extract(path)
    path.unlink()

    assert len(pages) == 1
    assert "Caf" in pages[0][1]


def test_get_extractor_pdf():
    from app.extractors.pdf_extractor import PdfExtractor
    ext = get_extractor("pdf")
    assert isinstance(ext, PdfExtractor)


def test_get_extractor_txt():
    ext = get_extractor("txt")
    assert isinstance(ext, TxtExtractor)


def test_get_extractor_unsupported():
    with pytest.raises(ValueError, match="not supported"):
        get_extractor("xyz")
