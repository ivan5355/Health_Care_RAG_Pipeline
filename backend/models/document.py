from datetime import datetime

from pydantic import BaseModel


class DocumentChunk(BaseModel):
    id: str
    document_id: str
    section_name: str
    text: str
    chunk_index: int


class Document(BaseModel):
    id: str
    name: str
    upload_date: datetime
    status: str  # "processing", "ready", "error"
    chunk_count: int
    raw_text: str


class DocumentDetail(Document):
    chunks: list[DocumentChunk]


class DocumentListResponse(BaseModel):
    documents: list[Document]
