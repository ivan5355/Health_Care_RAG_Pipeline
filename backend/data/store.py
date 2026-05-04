import os
import uuid
from datetime import datetime, timezone
from models.document import Document, DocumentChunk, DocumentDetail
from services.chunker import chunk_eob_by_section, extract_patient_name
from services.embeddings import generate_embeddings_batch
from services.pinecone_store import upsert_chunks, delete_by_document

documents: dict[str, DocumentDetail] = {}


def ingest_document(name: str, raw_text: str) -> DocumentDetail:
    doc_id = uuid.uuid4().hex[:12]

    chunks_raw = chunk_eob_by_section(doc_id, raw_text)
    patient_name = extract_patient_name(raw_text)

    chunk_texts = [c["text"] for c in chunks_raw]
    embeddings = generate_embeddings_batch(chunk_texts)

    upsert_chunks(chunks_raw, embeddings, document_name=name, patient_name=patient_name)

    chunks = [
        DocumentChunk(
            id=c["id"],
            document_id=c["document_id"],
            section_name=c["section_name"],
            text=c["text"],
            chunk_index=c["chunk_index"],
        )
        for c in chunks_raw
    ]

    doc = DocumentDetail(
        id=doc_id,
        name=name,
        upload_date=datetime.now(timezone.utc),
        status="ready",
        chunk_count=len(chunks),
        raw_text=raw_text,
        chunks=chunks,
    )

    documents[doc_id] = doc
    return doc


def get_all_documents() -> list[Document]:
    return [
        Document(
            id=d.id,
            name=d.name,
            upload_date=d.upload_date,
            status=d.status,
            chunk_count=d.chunk_count,
            raw_text=d.raw_text,
        )
        for d in documents.values()
    ]


def get_document(doc_id: str) -> DocumentDetail | None:
    return documents.get(doc_id)


def remove_document(doc_id: str) -> bool:
    if doc_id in documents:
        delete_by_document(doc_id)
        del documents[doc_id]
        return True
    return False


def _find_sample_eobs() -> list[str]:
    eob_dir = os.getenv("SAMPLE_EOB_DIR", "")
    if eob_dir and os.path.isdir(eob_dir):
        return sorted(
            os.path.join(eob_dir, f)
            for f in os.listdir(eob_dir)
            if f.endswith(".txt")
        )
    # Fallback: single file from old env var
    env_path = os.getenv("SAMPLE_EOB_PATH")
    if env_path and os.path.exists(env_path):
        return [env_path]
    fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sample_eob.txt"))
    if os.path.exists(fallback):
        return [fallback]
    return []


def load_sample_eob():
    import logging
    logger = logging.getLogger(__name__)

    from services.pinecone_store import get_pinecone_index
    try:
        idx = get_pinecone_index()
        stats = idx.describe_index_stats()
    except Exception as exc:
        logger.warning("Could not connect to Pinecone on startup: %s", exc)
        return

    sample_paths = _find_sample_eobs()
    if not sample_paths:
        return

    expected_count = 0
    for path in sample_paths:
        with open(path) as f:
            text = f.read()
        expected_count += len(chunk_eob_by_section("count", text))

    # If vectors already exist with correct count, just register in memory
    if stats.total_vector_count >= expected_count:
        logger.info("Pinecone already has %d vectors, registering %d documents in memory",
                     stats.total_vector_count, len(sample_paths))
        for path in sample_paths:
            name = os.path.basename(path)
            doc_id = name.replace(".txt", "").replace(".", "_")
            with open(path) as f:
                text = f.read()
            chunks_raw = chunk_eob_by_section(doc_id, text)
            chunks = [
                DocumentChunk(id=c["id"], document_id=c["document_id"],
                              section_name=c["section_name"], text=c["text"],
                              chunk_index=c["chunk_index"])
                for c in chunks_raw
            ]
            doc = DocumentDetail(
                id=doc_id, name=name,
                upload_date=datetime.now(timezone.utc), status="ready",
                chunk_count=len(chunks), raw_text=text, chunks=chunks,
            )
            documents[doc_id] = doc
        return

    # Otherwise, clear and re-ingest all
    try:
        if stats.total_vector_count > 0:
            idx.delete(delete_all=True)
        for path in sample_paths:
            name = os.path.basename(path)
            with open(path) as f:
                text = f.read()
            ingest_document(name, text)
            logger.info("Ingested sample EOB: %s", name)
    except Exception as exc:
        logger.warning("Could not ingest sample EOBs on startup (Bedrock unreachable?): %s", exc)
        logger.info("The API is running — upload documents manually via /api/documents/upload")
