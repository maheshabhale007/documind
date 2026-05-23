import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.models.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService

router = APIRouter()


def _get_service(request: Request, model_override: str | None = None) -> QueryService:
    return QueryService(
        embedding=request.app.state.embedding,
        vectorstore=request.app.state.vectorstore,
        model_override=model_override,
    )


@router.post("/", response_model=QueryResponse)
async def query(request: Request, body: QueryRequest):
    """Non-streaming Q&A. Returns full answer + citations."""
    service = _get_service(request, model_override=body.model)
    try:
        return await service.query(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def query_stream(request: Request, body: QueryRequest):
    """
    Streaming Q&A via Server-Sent Events (SSE).
    Event types:
      data: {"type": "token", "content": "..."}
      data: {"type": "citations", "data": [...]}
      data: {"type": "done"}
    """
    service = _get_service(request, model_override=body.model)

    async def event_generator():
        try:
            async for event in service.query_stream(body):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
