from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


@dataclass
class TextChunk:
    text: str
    chunk_index: int
    page: int  # 0 if unknown


class Chunker:
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.chunk_size,
            chunk_overlap=chunk_overlap or settings.chunk_overlap,
            length_function=len,
        )

    def split(self, text: str, page: int = 0) -> list[TextChunk]:
        """Split text into overlapping chunks. Page is passed through as metadata."""
        raw_chunks = self._splitter.split_text(text)
        return [
            TextChunk(text=chunk, chunk_index=i, page=page)
            for i, chunk in enumerate(raw_chunks)
        ]

    def split_pages(self, pages: list[tuple[int, str]]) -> list[TextChunk]:
        """
        Split multi-page text preserving page numbers.
        pages: list of (page_number, page_text) tuples.
        """
        chunks: list[TextChunk] = []
        global_index = 0
        for page_num, page_text in pages:
            page_chunks = self._splitter.split_text(page_text)
            for chunk_text in page_chunks:
                chunks.append(TextChunk(text=chunk_text, chunk_index=global_index, page=page_num))
                global_index += 1
        return chunks
