from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    model: str | None = None  # Override the default Ollama model


class Citation(BaseModel):
    filename: str
    page: int
    chunk_index: int
    relevance_score: float
    excerpt: str  # First 200 chars of the chunk


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    model_used: str
