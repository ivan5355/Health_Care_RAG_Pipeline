from datetime import datetime

from pydantic import BaseModel


class RetrievalMetrics(BaseModel):
    precision_at_k: dict[str, float]  # {"1": 1.0, "3": 0.67, "5": 0.60}
    recall_at_k: dict[str, float]
    mrr: float


class GenerationMetrics(BaseModel):
    faithfulness: float
    relevance: float
    completeness: float


class PerFieldMetric(BaseModel):
    field_name: str
    correct: int
    total: int
    accuracy: float


class StratifiedMetric(BaseModel):
    group_name: str
    group_value: str
    count: int
    avg_relevance: float
    avg_completeness: float
    avg_faithfulness: float
    field_accuracy: float


class JudgeMetrics(BaseModel):
    avg_correctness: float
    avg_completeness: float
    avg_grounding: float


class EvaluationRun(BaseModel):
    id: str
    name: str
    timestamp: datetime
    query_count: int
    avg_latency_ms: float
    retrieval_metrics: RetrievalMetrics
    generation_metrics: GenerationMetrics


class EvaluationRunDetail(EvaluationRun):
    queries: list[dict]
    latency_per_query: list[float]
    cost_per_query: list[float]
    per_field_metrics: list[PerFieldMetric] = []
    stratified_metrics: list[StratifiedMetric] = []
    judge_metrics: JudgeMetrics | None = None
    prompt_version: str = ""
    model_id: str = ""
    golden_dataset_version: str = ""
