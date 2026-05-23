from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.embedding import EmbeddingService
from app.core.vectorstore import VectorStoreService
from app.api.v1.router import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize services once and store on app.state
    app.state.embedding = EmbeddingService(model_name=settings.embedding_model)
    app.state.vectorstore = VectorStoreService(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_name=settings.chroma_collection,
    )
    yield
    # Shutdown: nothing to clean up for these services


app = FastAPI(
    title="DocuMind API",
    description="Local-first RAG platform — chat with your documents, no API keys needed.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")
