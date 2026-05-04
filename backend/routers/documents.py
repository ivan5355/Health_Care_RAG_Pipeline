import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from models.document import Document, DocumentDetail, DocumentListResponse
from data.store import get_all_documents, get_document, ingest_document, remove_document
from auth import User, get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents(user: User = Depends(get_current_user)):
    return DocumentListResponse(documents=get_all_documents())


@router.post("/upload", response_model=DocumentDetail)
async def upload_document(file: UploadFile = File(...), user: User = Depends(require_admin)):
    content = await file.read()
    raw_text = content.decode("utf-8")
    logger.info("Ingesting document", extra={"document_id": file.filename})
    doc = ingest_document(file.filename or "untitled.txt", raw_text)
    logger.info("Document ingested", extra={"document_id": doc.id})
    return doc


@router.get("/{doc_id}", response_model=DocumentDetail)
def get_document_detail(doc_id: str, user: User = Depends(get_current_user)):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{doc_id}")
def delete_document(doc_id: str, user: User = Depends(require_admin)):
    if not remove_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted"}
