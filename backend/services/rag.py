import hashlib
import json
import logging
import time
from services.bedrock_client import converse
from services.embeddings import generate_embedding
from services.pinecone_store import query_similar
from services import prompt_manager
from models.chat import RAGResponse, RAGAnswer, SourceChunk, QueryMetadata

logger = logging.getLogger(__name__)

COST_PER_INPUT_TOKEN = 0.000003
COST_PER_OUTPUT_TOKEN = 0.000015


def _parse_structured(raw: str) -> RAGAnswer | None:
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            return None
        data = json.loads(raw[start:end])
        return RAGAnswer(
            reasoning=data.get("reasoning", ""),
            answer=data.get("answer", raw),
            citations=data.get("citations", []),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.warning("Could not parse structured response, falling back to raw text")
        return None


def generate_answer(question: str, chunks: list[dict], version: str | None = None) -> tuple[str, int, RAGAnswer | None, str]:
    messages, system, inference_config, prompt_version = prompt_manager.build_messages(
        question, chunks, version=version,
    )
    model_id = prompt_manager.get_model_id(version)

    input_hash = hashlib.sha256(
        json.dumps(messages, sort_keys=True).encode()
    ).hexdigest()

    start = time.time()
    response = converse(
        model_id=model_id,
        messages=messages,
        system=system,
        inference_config=inference_config,
    )
    llm_latency_ms = round((time.time() - start) * 1000, 1)

    raw_answer = response["output"]["message"]["content"][0]["text"]
    input_tokens = response["usage"]["inputTokens"]
    output_tokens = response["usage"]["outputTokens"]
    total_tokens = input_tokens + output_tokens
    cost = round(input_tokens * COST_PER_INPUT_TOKEN + output_tokens * COST_PER_OUTPUT_TOKEN, 6)

    logger.info(
        "LLM invocation",
        extra={
            "prompt_version": prompt_version,
            "model_id": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "latency_ms": llm_latency_ms,
            "cost_estimate": cost,
            "input_hash": input_hash,
        },
    )

    structured = _parse_structured(raw_answer)
    display_answer = structured.answer if structured else raw_answer

    return display_answer, total_tokens, structured, prompt_version


def query_rag(question: str, top_k: int = 5, document_ids: list[str] | None = None) -> RAGResponse:
    retrieval_start = time.time()

    query_embedding = generate_embedding(question)

    filter_dict = None
    if document_ids:
        filter_dict = {"document_id": {"$in": document_ids}}

    matches = query_similar(query_embedding, top_k=top_k, filter_dict=filter_dict)
    retrieval_latency = (time.time() - retrieval_start) * 1000

    sources = []
    chunks_for_generation = []
    for match in matches:
        meta = match.metadata
        patient_name = meta.get("patient_name", "Unknown")
        sources.append(
            SourceChunk(
                chunk_id=match.id,
                document_name=meta.get("document_name", "unknown"),
                section_name=meta.get("section_name", "Unknown"),
                text=meta.get("text", ""),
                similarity_score=round(match.score, 4),
                chunk_index=meta.get("chunk_index", 0),
                patient_name=patient_name,
            )
        )
        chunks_for_generation.append({
            "section_name": meta.get("section_name", "Unknown"),
            "text": meta.get("text", ""),
            "patient_name": patient_name,
        })

    generation_start = time.time()

    structured = None
    prompt_version = ""
    if chunks_for_generation:
        answer, total_tokens, structured, prompt_version = generate_answer(question, chunks_for_generation)
    else:
        answer = "I couldn't find relevant information in the uploaded documents to answer this question."
        total_tokens = 0

    generation_latency = (time.time() - generation_start) * 1000
    model_id = prompt_manager.get_model_id()

    return RAGResponse(
        answer=answer,
        structured=structured,
        sources=sources,
        metadata=QueryMetadata(
            retrieval_latency_ms=round(retrieval_latency, 1),
            generation_latency_ms=round(generation_latency, 1),
            total_latency_ms=round(retrieval_latency + generation_latency, 1),
            total_tokens=total_tokens,
            model=model_id,
            prompt_version=prompt_version,
        ),
    )
