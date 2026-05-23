import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles

from app.config import settings
from app.core.chunker import Chunker
from app.core.embedding import EmbeddingService
from app.core.vectorstore import VectorStoreService
from app.extractors.base import get_extractor
from app.models.document import DocumentMeta


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}
MAX_BYTES = settings.max_file_size_mb * 1024 * 1024


class DocumentService:
    def __init__(self, embedding: EmbeddingService, vectorstore: VectorStoreService):
        self._embedding = embedding
        self._vectorstore = vectorstore
        self._chunker = Chunker()
        self._upload_dir = Path(settings.upload_dir)
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    async def ingest(self, filename: str, content: bytes) -> DocumentMeta:
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File type '{suffix}' not supported. Allowed: {ALLOWED_EXTENSIONS}")
        if len(content) > MAX_BYTES:
            raise ValueError(f"File exceeds {settings.max_file_size_mb} MB limit.")

        document_id = str(uuid.uuid4())
        safe_name = f"{document_id}_{filename}"
        dest = self._upload_dir / safe_name

        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)

        extractor = get_extractor(suffix)
        pages = extractor.extract(dest)

        chunks = self._chunker.split_pages(pages)
        if not chunks:
            dest.unlink(missing_ok=True)
            raise ValueError("No text could be extracted from the file.")

        # Batch embed all chunks in one call (10x faster than one at a time)
        texts = [c.text for c in chunks]
        embeddings = self._embedding.embed_texts(texts)

        ingested_at = datetime.now(timezone.utc).isoformat()
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "filename": filename,
                "file_type": suffix.lstrip("."),
                "page": chunk.page,
                "chunk_index": chunk.chunk_index,
                "total_chunks": len(chunks),
                "ingested_at": ingested_at,
            }
            for chunk in chunks
        ]

        self._vectorstore.add_documents(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        return DocumentMeta(
            document_id=document_id,
            filename=filename,
            file_type=suffix.lstrip("."),
            total_chunks=len(chunks),
            ingested_at=ingested_at,
        )

    def list_documents(self) -> list[dict]:
        return self._vectorstore.list_documents()

    def delete_document(self, document_id: str) -> bool:
        self._vectorstore.delete_document(document_id)
        # Also remove the uploaded file if it exists
        for f in self._upload_dir.glob(f"{document_id}_*"):
            f.unlink(missing_ok=True)
        return True
