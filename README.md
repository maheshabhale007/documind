# DocuMind

**Local-first document intelligence — chat with your PDFs, DOCX, and TXT files. No API keys. No data leaves your machine.**

DocuMind is a production-grade RAG (Retrieval-Augmented Generation) platform. Upload documents, ask questions, and get cited answers powered by a local LLM running entirely on your hardware.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER                           │
│  Streamlit UI (8501)          REST API / Swagger (8000)     │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                     │
│                                                             │
│  Document Service          Query Service                    │
│  ├─ File validation        ├─ Embed query                   │
│  ├─ Text extraction        ├─ Vector similarity search      │
│  ├─ Semantic chunking      ├─ Prompt building               │
│  └─ Batch embedding        └─ SSE streaming response        │
│                                                             │
│  EmbeddingService          VectorStoreService  LLMService   │
│  (sentence-transformers)   (ChromaDB client)  (Ollama HTTP) │
└──────────┬─────────────────────┬──────────────────┬─────────┘
           │                     │                  │
           ▼                     ▼                  ▼
    sentence-transformers    ChromaDB (8200)    Ollama (11434)
    all-MiniLM-L6-v2         Persistent         llama3.2:3b
    384-dim vectors           vector store       mistral:7b
```

### Data Flow: Ingestion
```
Upload → Extract text (PyMuPDF / python-docx / chardet)
       → Chunk (RecursiveCharacterTextSplitter, 512 tokens, 64 overlap)
       → Batch embed (all-MiniLM-L6-v2, single encode() call)
       → Store in ChromaDB with metadata {filename, page, chunk_index}
```

### Data Flow: Query
```
Question → Embed → ChromaDB similarity search (top-5)
         → Build prompt with context + citations
         → Stream from Ollama → SSE tokens → UI
         → Return citations {filename, page, relevance_score}
```

---

## Quickstart

**Prerequisites:** Docker + Docker Compose

```bash
# 1. Clone and configure
git clone https://github.com/mahesh-abhale/documind
cd documind
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Pull the LLM (one-time, ~2GB download)
make pull-models

# 4. Open the UI
open http://localhost:8501
```

That's it. Upload a document and start asking questions.

---

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Streamlit UI | http://localhost:8501 | Chat interface |
| FastAPI backend | http://localhost:8000 | REST API |
| Swagger docs | http://localhost:8000/docs | Interactive API explorer |
| ChromaDB | http://localhost:8200 | Vector database |
| Ollama | http://localhost:11434 | Local LLM server |

---

## API Usage

### Upload a document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@/path/to/your/document.pdf"
```

### Ask a question (non-streaming)
```bash
curl -X POST http://localhost:8000/api/v1/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main contribution of this paper?", "top_k": 5}'
```

### Ask a question (streaming SSE)
```bash
curl -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize the methodology", "top_k": 5}'
```

### List documents
```bash
curl http://localhost:8000/api/v1/documents/
```

### Delete a document
```bash
curl -X DELETE http://localhost:8000/api/v1/documents/{document_id}
```

### Health check
```bash
curl http://localhost:8000/api/v1/health | python -m json.tool
```

---

## Supported File Types

| Format | Extractor | Page numbers |
|--------|-----------|-------------|
| PDF | PyMuPDF (fitz) | Yes |
| DOCX | python-docx | No (whole doc) |
| TXT / MD | chardet + read | No |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM runtime | [Ollama](https://ollama.com) · llama3.2:3b / mistral:7b |
| Embeddings | sentence-transformers · all-MiniLM-L6-v2 (384-dim) |
| Vector database | ChromaDB (cosine similarity, persistent) |
| Backend | FastAPI · async Python · Pydantic v2 |
| Streaming | Server-Sent Events (SSE) · FastAPI StreamingResponse |
| Chunking | LangChain RecursiveCharacterTextSplitter |
| UI | Streamlit |
| Infrastructure | Docker Compose |

---

## Key Engineering Decisions

**Batch embeddings** — All chunks from a document are embedded in a single `model.encode(chunks)` call. This is ~10x faster than embedding one chunk at a time because the model processes them as a batch on the same forward pass.

**Same model for ingestion and query** — The `EmbeddingService` singleton is used for both document chunks and query strings. Using different models would produce vectors in different semantic spaces, making similarity search meaningless. This is a common bug in naive RAG implementations.

**Ollama's OpenAI-compatible API** — Switching from local Ollama to OpenAI requires only changing `OLLAMA_BASE_URL` and adding an API key. The interface is identical.

**ChromaDB over FAISS** — FAISS requires manual serialization for persistence and doesn't support metadata filtering. ChromaDB runs as a proper service with a client-server architecture, handles restarts gracefully, and supports filtering results by filename/document ID.

**Chunk overlap** — 64-token overlap between chunks prevents answers from being split across chunk boundaries. Without overlap, a sentence spanning two chunks would be missing from both retrieval results.

---

## Running Tests

```bash
make test
# or directly:
docker compose run --rm backend pytest app/tests/ -v
```

---

## Configuration

All settings via environment variables (`.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.2:3b` | LLM to use (must be pulled first) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model |
| `CHUNK_SIZE` | `512` | Max chars per chunk |
| `CHUNK_OVERLAP` | `64` | Overlap between chunks |
| `TOP_K_RESULTS` | `5` | Chunks retrieved per query |
| `MAX_FILE_SIZE_MB` | `50` | Upload size limit |

---

## Project Structure

```
documind/
├── backend/
│   └── app/
│       ├── api/v1/         # REST endpoints (health, documents, query)
│       ├── core/           # EmbeddingService, VectorStoreService, LLMService, Chunker
│       ├── services/       # DocumentService, QueryService (orchestration layer)
│       ├── extractors/     # PDF, DOCX, TXT text extractors
│       ├── models/         # Pydantic request/response models
│       └── tests/          # pytest test suite
├── frontend/
│   ├── app.py              # Streamlit entry point
│   └── components/         # sidebar, chat, citations
├── scripts/                # pull_models.sh, seed_demo.sh
├── sample_docs/            # Demo documents
└── docker-compose.yml
```

---

## License

MIT
