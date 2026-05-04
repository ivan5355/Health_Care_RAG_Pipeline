import asyncio
import logging

from fastapi import APIRouter, Depends

from auth import User, get_current_user
from models.chat import RAGQuery, RAGResponse
from services.rag import query_rag

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=RAGResponse)
async def handle_query(query: RAGQuery, user: User = Depends(get_current_user)):
    logger.info("RAG query received", extra={"question": query.question})
    response = await asyncio.to_thread(
        query_rag,
        question=query.question,
        top_k=query.top_k,
        document_ids=query.document_ids,
    )
    return response
