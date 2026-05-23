from dataclasses import dataclass

import chromadb
from chromadb.config import Settings


@dataclass
class QueryResult:
    ids: list[str]
    documents: list[str]
    metadatas: list[dict]
    distances: list[float]


class VectorStoreService:
    def __init__(self, host: str, port: int, collection_name: str):
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection_name = collection_name
        self._collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(self, query_embedding: list[float], n_results: int = 5) -> QueryResult:
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        return QueryResult(
            ids=results["ids"][0],
            documents=results["documents"][0],
            metadatas=results["metadatas"][0],
            distances=results["distances"][0],
        )

    def delete_document(self, document_id: str) -> None:
        """Delete all chunks belonging to a document by its document_id metadata field."""
        results = self._collection.get(where={"document_id": document_id})
        if results["ids"]:
            self._collection.delete(ids=results["ids"])

    def list_documents(self) -> list[dict]:
        """Return one metadata record per unique document_id."""
        all_items = self._collection.get(include=["metadatas"])
        seen: dict[str, dict] = {}
        for meta in all_items["metadatas"]:
            doc_id = meta.get("document_id")
            if doc_id and doc_id not in seen:
                seen[doc_id] = meta
        return list(seen.values())

    def get_collection_stats(self) -> dict:
        count = self._collection.count()
        return {"collection": self.collection_name, "total_chunks": count}
