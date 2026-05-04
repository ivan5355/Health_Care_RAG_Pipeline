import logging
import os
import sys
import time
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from data.store import load_sample_eob  # noqa: E402
from logging_config import correlation_id_var, setup_logging  # noqa: E402
from routers import auth, documents, evaluations, prompts, query  # noqa: E402

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Healthcare RAG API")
    load_sample_eob()
    logger.info("Sample EOB loaded")
    yield
    logger.info("Shutting down Healthcare RAG API")


app = FastAPI(
    title="Healthcare RAG API",
    description="RAG pipeline for healthcare document Q&A",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175", "http://frontend:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID", uuid.uuid4().hex)
    correlation_id_var.set(cid)

    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 1)

    response.headers["X-Correlation-ID"] = cid

    logger.info(
        "Request completed",
        extra={
            "correlation_id": cid,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(evaluations.router)
app.include_router(prompts.router)


@app.get("/api/health")
def health_check():
    status = "ok"
    checks = {}

    try:
        from services.pinecone_store import get_pinecone_index

        get_pinecone_index().describe_index_stats()
        checks["pinecone"] = "ok"
    except Exception as e:
        checks["pinecone"] = f"error: {e}"
        status = "degraded"

    bedrock_key = os.getenv("BEDROCK_API_KEY", "")
    if bedrock_key:
        checks["bedrock"] = "configured"
    else:
        checks["bedrock"] = "missing_key"
        status = "degraded"

    return {"status": status, "checks": checks}
