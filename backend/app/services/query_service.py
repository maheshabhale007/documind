from collections.abc import AsyncGenerator

from app.config import settings
from app.core.embedding import EmbeddingService
from app.core.llm import LLMService
from app.core.vectorstore import VectorStoreService
from app.models.query import Citation, QueryRequest, QueryResponse

PROMPT_TEMPLATE = """You are a helpful document assistant. Answer the user's question using ONLY the context provided below.
If the context does not contain enough information to answer, say "I don't have enough information in the provided documents to answer this."
Cite your sources inline using [filename, page N] notation.

Context:
{context}

Question: {query}

Answer:"""


def _build_context(documents: list[str], metadatas: list[dict]) -> str:
    parts = []
    for doc, meta in zip(documents, metadatas):
        filename = meta.get("filename", "unknown")
        page = meta.get("page", 0)
        parts.append(f"[{filename}, page {page}]\n{doc}")
    return "\n\n---\n\n".join(parts)


def _build_citations(
    documents: list[str], metadatas: list[dict], distances: list[float]
) -> list[Citation]:
    citations = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        relevance = round(1.0 - dist, 4)  # cosine distance → similarity
        citations.append(
            Citation(
                filename=meta.get("filename", "unknown"),
                page=meta.get("page", 0),
                chunk_index=meta.get("chunk_index", 0),
                relevance_score=relevance,
                excerpt=doc[:200],
            )
        )
    return citations


class QueryService:
    def __init__(
        self,
        embedding: EmbeddingService,
        vectorstore: VectorStoreService,
        model_override: str | None = None,
    ):
        self._embedding = embedding
        self._vectorstore = vectorstore
        self._llm = LLMService(model=model_override or settings.ollama_model)

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Non-streaming query — waits for full LLM response."""
        query_vec = self._embedding.embed_query(request.query)
        results = self._vectorstore.query(query_vec, n_results=request.top_k)

        context = _build_context(results.documents, results.metadatas)
        prompt = PROMPT_TEMPLATE.format(context=context, query=request.query)

        answer = await self._llm.generate(prompt)
        citations = _build_citations(results.documents, results.metadatas, results.distances)

        return QueryResponse(
            answer=answer,
            citations=citations,
            model_used=self._llm.model,
        )

    async def query_stream(
        self, request: QueryRequest
    ) -> AsyncGenerator[dict, None]:
        """
        Streaming query. Yields dicts:
          {"type": "token", "content": "..."}     — for each token
          {"type": "citations", "data": [...]}    — at the end
          {"type": "done"}                         — signals stream end
        """
        query_vec = self._embedding.embed_query(request.query)
        results = self._vectorstore.query(query_vec, n_results=request.top_k)

        context = _build_context(results.documents, results.metadatas)
        prompt = PROMPT_TEMPLATE.format(context=context, query=request.query)

        async for token in self._llm.generate_stream(prompt):
            yield {"type": "token", "content": token}

        citations = _build_citations(results.documents, results.metadatas, results.distances)
        yield {"type": "citations", "data": [c.model_dump() for c in citations]}
        yield {"type": "done"}
