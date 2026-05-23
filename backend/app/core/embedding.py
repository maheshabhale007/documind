from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Loaded once at startup via lifespan — not per-request
        self._model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch embed a list of text strings. Always use this for document chunks."""
        vectors = self._model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return vectors.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string. Must use the same model as embed_texts."""
        vector = self._model.encode([query], show_progress_bar=False, convert_to_numpy=True)
        return vector[0].tolist()
