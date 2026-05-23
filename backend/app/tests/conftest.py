import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.core.embedding import EmbeddingService
from app.core.vectorstore import VectorStoreService


@pytest.fixture(scope="session")
def mock_embedding():
    svc = MagicMock(spec=EmbeddingService)
    svc.embed_texts.return_value = [[0.1] * 384]
    svc.embed_query.return_value = [0.1] * 384
    return svc


@pytest.fixture(scope="session")
def mock_vectorstore():
    from app.core.vectorstore import QueryResult
    svc = MagicMock(spec=VectorStoreService)
    svc.client = MagicMock()
    svc.client.heartbeat.return_value = True
    svc.add_documents.return_value = None
    svc.query.return_value = QueryResult(
        ids=["doc1_0"],
        documents=["The attention mechanism is the key contribution."],
        metadatas=[{
            "document_id": "doc1",
            "filename": "test.pdf",
            "file_type": "pdf",
            "page": 1,
            "chunk_index": 0,
            "total_chunks": 1,
            "ingested_at": "2025-01-01T00:00:00Z",
        }],
        distances=[0.1],
    )
    svc.list_documents.return_value = [{
        "document_id": "doc1",
        "filename": "test.pdf",
        "file_type": "pdf",
        "total_chunks": 1,
        "ingested_at": "2025-01-01T00:00:00Z",
    }]
    svc.delete_document.return_value = None
    return svc


@pytest.fixture(scope="session")
def client(mock_embedding, mock_vectorstore):
    app.state.embedding = mock_embedding
    app.state.vectorstore = mock_vectorstore
    with TestClient(app) as c:
        yield c
