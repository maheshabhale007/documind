from fastapi import APIRouter, HTTPException, Request, UploadFile, File

from app.models.document import DocumentMeta, DocumentListItem, DeleteResponse
from app.services.document_service import DocumentService

router = APIRouter()


def _get_service(request: Request) -> DocumentService:
    return DocumentService(
        embedding=request.app.state.embedding,
        vectorstore=request.app.state.vectorstore,
    )


@router.post("/upload", response_model=DocumentMeta, status_code=201)
async def upload_document(request: Request, file: UploadFile = File(...)):
    service = _get_service(request)
    content = await file.read()
    try:
        meta = await service.ingest(filename=file.filename, content=content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return meta


@router.get("/", response_model=list[DocumentListItem])
def list_documents(request: Request):
    service = _get_service(request)
    docs = service.list_documents()
    return [DocumentListItem(**d) for d in docs]


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(document_id: str, request: Request):
    service = _get_service(request)
    service.delete_document(document_id)
    return DeleteResponse(
        document_id=document_id,
        deleted=True,
        message=f"Document {document_id} and all its chunks have been removed.",
    )
