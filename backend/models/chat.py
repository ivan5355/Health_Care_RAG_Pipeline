from pydantic import BaseModel


class RAGQuery(BaseModel):
    question: str
    top_k: int = 5
    document_ids: list[str] | None = None


class SourceChunk(BaseModel):
    chunk_id: str
    document_name: str
    section_name: str
    text: str
    similarity_score: float
    chunk_index: int
    patient_name: str


class QueryMetadata(BaseModel):
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float
    total_tokens: int
    model: str
    prompt_version: str = ""


class RAGAnswer(BaseModel):
    reasoning: str
    answer: str
    citations: list[int]


class RAGResponse(BaseModel):
    answer: str
    structured: RAGAnswer | None = None
    sources: list[SourceChunk]
    metadata: QueryMetadata
