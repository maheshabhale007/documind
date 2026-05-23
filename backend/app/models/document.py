from datetime import datetime

from pydantic import BaseModel


class DocumentMeta(BaseModel):
    document_id: str
    filename: str
    file_type: str
    total_chunks: int
    ingested_at: str


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    file_type: str
    total_chunks: int
    ingested_at: str


class DeleteResponse(BaseModel):
    document_id: str
    deleted: bool
    message: str
