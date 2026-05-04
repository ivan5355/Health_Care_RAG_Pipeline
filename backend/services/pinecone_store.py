import os
from pinecone import Pinecone, ServerlessSpec

_pc = None
_index = None

INDEX_NAME = "healthcare-rag"
DIMENSION = 1024


def get_pinecone_index():
    global _pc, _index
    if _index is None:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")

        _pc = Pinecone(api_key=api_key)

        existing = [idx.name for idx in _pc.list_indexes()]
        if INDEX_NAME not in existing:
            _pc.create_index(
                name=INDEX_NAME,
                dimension=DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

        _index = _pc.Index(INDEX_NAME)
    return _index


def upsert_chunks(chunks: list[dict], embeddings: list[list[float]], document_name: str = "unknown", patient_name: str = "Unknown"):
    index = get_pinecone_index()
    vectors = []
    for chunk, embedding in zip(chunks, embeddings):
        vectors.append(
            {
                "id": chunk["id"],
                "values": embedding,
                "metadata": {
                    "document_id": chunk["document_id"],
                    "document_name": document_name,
                    "section_name": chunk["section_name"],
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"][:1000],
                    "patient_name": patient_name,
                },
            }
        )
    index.upsert(vectors=vectors)


def query_similar(query_embedding: list[float], top_k: int = 5, filter_dict: dict | None = None):
    index = get_pinecone_index()
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter_dict,
    )
    return results.matches


def delete_by_document(document_id: str):
    index = get_pinecone_index()
    index.delete(filter={"document_id": {"$eq": document_id}})
