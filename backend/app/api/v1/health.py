import httpx
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    config = request.app.state
    statuses = {}

    # Check embedding model
    try:
        test_vec = request.app.state.embedding.embed_query("ping")
        statuses["embedding"] = "ok" if test_vec else "error"
    except Exception as e:
        statuses["embedding"] = f"error: {e}"

    # Check ChromaDB
    try:
        request.app.state.vectorstore.client.heartbeat()
        statuses["chromadb"] = "ok"
    except Exception as e:
        statuses["chromadb"] = f"error: {e}"

    # Check Ollama
    try:
        from app.config import settings
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            statuses["ollama"] = "ok" if resp.status_code == 200 else f"http {resp.status_code}"
    except Exception as e:
        statuses["ollama"] = f"error: {e}"

    overall = "ok" if all(v == "ok" for v in statuses.values()) else "degraded"
    return {"status": overall, "services": statuses}
