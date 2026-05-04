import json
import logging
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import yaml

from models.evaluation import (
    EvaluationRun,
    EvaluationRunDetail,
    GenerationMetrics,
    JudgeMetrics,
    PerFieldMetric,
    RetrievalMetrics,
    StratifiedMetric,
)
from services import prompt_manager
from services.bedrock_client import converse
from services.rag import query_rag

logger = logging.getLogger(__name__)

GOLDEN_DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "golden_dataset.yaml"

eval_store: dict[str, EvaluationRunDetail] = {}


def _load_golden_dataset() -> tuple[list[dict], str]:
    with open(GOLDEN_DATASET_PATH) as f:
        data = yaml.safe_load(f)
    return data["examples"], data.get("version", "unknown")


def compute_precision_at_k(retrieved_sections: list[str], relevant_sections: list[str], k: int) -> float:
    top_k = retrieved_sections[:k]
    if not top_k:
        return 0.0
    relevant_set = set(s.upper() for s in relevant_sections)
    seen = set()
    hits = 0
    for s in top_k:
        key = s.upper()
        if key in relevant_set and key not in seen:
            hits += 1
            seen.add(key)
    return hits / len(top_k)


def compute_recall_at_k(retrieved_sections: list[str], relevant_sections: list[str], k: int) -> float:
    top_k = retrieved_sections[:k]
    relevant_set = set(s.upper() for s in relevant_sections)
    if not relevant_set:
        return 0.0
    found = set(s.upper() for s in top_k) & relevant_set
    return len(found) / len(relevant_set)


def compute_mrr(retrieved_sections: list[str], relevant_sections: list[str]) -> float:
    relevant_set = set(s.upper() for s in relevant_sections)
    for i, section in enumerate(retrieved_sections):
        if section.upper() in relevant_set:
            return 1.0 / (i + 1)
    return 0.0


def check_faithfulness(answer: str, source_texts: list[str]) -> float:
    combined_sources = " ".join(source_texts).lower()
    answer_words = [w for w in answer.lower().split() if len(w) > 3]
    if not answer_words:
        return 1.0
    grounded = sum(1 for w in answer_words if w in combined_sources)
    return grounded / len(answer_words)


def check_relevance(answer: str, expected: str) -> float:
    expected_parts = [p.strip().lower() for p in expected.replace(",", " ").split() if len(p.strip()) > 1]
    if not expected_parts:
        return 1.0
    found = sum(1 for p in expected_parts if p in answer.lower())
    return found / len(expected_parts)


def check_completeness(answer: str, expected: str) -> float:
    expected_values = [v.strip() for v in expected.split(",")]
    if not expected_values:
        return 1.0
    found = sum(1 for v in expected_values if v.strip().lower() in answer.lower())
    return found / len(expected_values)


def compute_per_field_accuracy(answer: str, expected_fields: dict) -> dict[str, bool]:
    results = {}
    for field_name, expected_value in expected_fields.items():
        results[field_name] = expected_value.lower() in answer.lower()
    return results


def _avg(lst: list[float]) -> float:
    return sum(lst) / len(lst) if lst else 0.0


JUDGE_MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"


def _call_judge(system_prompt: str, user_prompt: str) -> dict:
    response = converse(
        model_id=JUDGE_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        system=[{"text": system_prompt}],
        inference_config={"maxTokens": 300, "temperature": 0.0},
    )
    raw = response["output"]["message"]["content"][0]["text"]
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except (json.JSONDecodeError, ValueError):
        logger.warning("Could not parse judge response: %s", raw[:200])
        return {"score": 3, "reasoning": "Parse error — defaulted to 3"}


def judge_correctness(question: str, expected_answer: str, actual_answer: str) -> dict:
    system = (
        "You are evaluating whether an AI answer is semantically correct. "
        "Compare the actual answer to the expected answer. They don't need to match word-for-word — "
        "focus on whether the facts, numbers, and meaning are equivalent.\n\n"
        "Score 1-5:\n"
        "1 = completely wrong\n"
        "2 = mostly wrong, minor overlap\n"
        "3 = partially correct\n"
        "4 = mostly correct, minor errors\n"
        "5 = fully correct\n\n"
        'Respond with JSON only: {"score": <int>, "reasoning": "<brief explanation>"}'
    )
    user = f"Question: {question}\n\nExpected answer: {expected_answer}\n\nActual answer: {actual_answer}"
    return _call_judge(system, user)


def judge_completeness(question: str, expected_answer: str, actual_answer: str) -> dict:
    system = (
        "You are evaluating whether an AI answer is complete. "
        "The expected answer contains key facts. Score how many of those facts appear "
        "in the actual answer, even if worded differently.\n\n"
        "Score 1-5:\n"
        "1 = missing all key facts\n"
        "2 = has one or two facts, missing most\n"
        "3 = has about half the key facts\n"
        "4 = has most key facts, missing one or two\n"
        "5 = all key facts present\n\n"
        'Respond with JSON only: {"score": <int>, "reasoning": "<brief explanation>"}'
    )
    user = f"Question: {question}\n\nExpected answer: {expected_answer}\n\nActual answer: {actual_answer}"
    return _call_judge(system, user)


def judge_grounding(question: str, actual_answer: str, source_texts: list[str]) -> dict:
    sources_combined = "\n---\n".join(source_texts)
    system = (
        "You are evaluating whether an AI answer is grounded in the provided source documents. "
        "Every claim in the answer must be supported by the sources. Flag any hallucinated facts.\n\n"
        "Score 1-5:\n"
        "1 = mostly hallucinated, not supported by sources\n"
        "2 = significant unsupported claims\n"
        "3 = mixed — some grounded, some not\n"
        "4 = mostly grounded, minor unsupported details\n"
        "5 = fully grounded in sources\n\n"
        'Respond with JSON only: {"score": <int>, "reasoning": "<brief explanation>"}'
    )
    user = f"Question: {question}\n\nActual answer: {actual_answer}\n\nSource documents:\n{sources_combined}"
    return _call_judge(system, user)


def run_evaluation(name: str = "RAG Evaluation", prompt_version: str | None = None) -> EvaluationRunDetail:
    golden_examples, dataset_version = _load_golden_dataset()

    if prompt_version is None:
        prompt_version = prompt_manager.resolve_version()
    model_id = prompt_manager.get_model_id(prompt_version)

    run_id = f"eval_{uuid.uuid4().hex[:8]}"
    queries_results = []
    latencies = []
    costs = []

    all_precisions: dict[int, list[float]] = {1: [], 3: [], 5: []}
    all_recalls: dict[int, list[float]] = {1: [], 3: [], 5: []}
    all_mrrs = []
    all_faithfulness = []
    all_relevance = []
    all_completeness = []
    all_judge_correctness = []
    all_judge_completeness = []
    all_judge_grounding = []

    # Per-field tracking
    field_correct: dict[str, int] = defaultdict(int)
    field_total: dict[str, int] = defaultdict(int)

    # Stratification tracking
    strat_results: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))

    for gt in golden_examples:
        start = time.time()
        response = query_rag(gt["question"], top_k=5)
        elapsed_ms = (time.time() - start) * 1000

        retrieved_sections = [s.section_name for s in response.sources]
        source_texts = [s.text for s in response.sources]

        for k in [1, 3, 5]:
            all_precisions[k].append(compute_precision_at_k(retrieved_sections, gt["relevant_sections"], k))
            all_recalls[k].append(compute_recall_at_k(retrieved_sections, gt["relevant_sections"], k))

        all_mrrs.append(compute_mrr(retrieved_sections, gt["relevant_sections"]))

        faithfulness = check_faithfulness(response.answer, source_texts)
        relevance = check_relevance(response.answer, gt["expected_answer"])
        completeness = check_completeness(response.answer, gt["expected_answer"])

        all_faithfulness.append(faithfulness)
        all_relevance.append(relevance)
        all_completeness.append(completeness)

        latencies.append(round(elapsed_ms, 1))
        estimated_cost = response.metadata.total_tokens * 0.000003
        costs.append(round(estimated_cost, 6))

        # Per-field accuracy
        field_results = {}
        expected_fields = gt.get("expected_fields", {})
        if expected_fields:
            field_results = compute_per_field_accuracy(response.answer, expected_fields)
            for field_name, correct in field_results.items():
                field_total[field_name] += 1
                if correct:
                    field_correct[field_name] += 1

        # Collect for stratification by category, document_type, payer
        result_entry = {
            "faithfulness": faithfulness,
            "relevance": relevance,
            "completeness": completeness,
            "field_results": field_results,
        }
        for group in ("category", "document_type", "payer"):
            group_val = gt.get(group, "unknown")
            strat_results[group][group_val].append(result_entry)

        # LLM-as-judge scoring
        try:
            j_correct = judge_correctness(gt["question"], gt["expected_answer"], response.answer)
            j_complete = judge_completeness(gt["question"], gt["expected_answer"], response.answer)
            j_ground = judge_grounding(gt["question"], response.answer, source_texts)
        except Exception as exc:
            logger.warning("Judge call failed for question %s: %s", gt.get("id", ""), exc)
            j_correct = {"score": 0, "reasoning": f"Judge error: {exc}"}
            j_complete = {"score": 0, "reasoning": f"Judge error: {exc}"}
            j_ground = {"score": 0, "reasoning": f"Judge error: {exc}"}

        all_judge_correctness.append(j_correct.get("score", 0))
        all_judge_completeness.append(j_complete.get("score", 0))
        all_judge_grounding.append(j_ground.get("score", 0))

        queries_results.append(
            {
                "id": gt.get("id", ""),
                "question": gt["question"],
                "expected": gt["expected_answer"],
                "answer": response.answer,
                "retrieved_sections": retrieved_sections,
                "category": gt.get("category", ""),
                "document_type": gt.get("document_type", ""),
                "payer": gt.get("payer", ""),
                "difficulty": gt.get("difficulty", ""),
                "edge_case": gt.get("edge_case", False),
                "field_results": field_results,
                "relevance": round(relevance, 4),
                "completeness": round(completeness, 4),
                "faithfulness": round(faithfulness, 4),
                "judge_correctness": j_correct.get("score", 0),
                "judge_correctness_reasoning": j_correct.get("reasoning", ""),
                "judge_completeness": j_complete.get("score", 0),
                "judge_completeness_reasoning": j_complete.get("reasoning", ""),
                "judge_grounding": j_ground.get("score", 0),
                "judge_grounding_reasoning": j_ground.get("reasoning", ""),
            }
        )

    # Build per-field metrics
    per_field = []
    for field_name in sorted(field_total.keys()):
        total = field_total[field_name]
        correct_count = field_correct[field_name]
        per_field.append(
            PerFieldMetric(
                field_name=field_name,
                correct=correct_count,
                total=total,
                accuracy=round(correct_count / total, 4) if total else 0.0,
            )
        )

    # Build stratified metrics
    stratified = []
    for group_name, group_values in sorted(strat_results.items()):
        for group_value, entries in sorted(group_values.items()):
            all_field_results = []
            for e in entries:
                all_field_results.extend(e["field_results"].values())
            field_acc = _avg([1.0 if v else 0.0 for v in all_field_results]) if all_field_results else 0.0

            stratified.append(
                StratifiedMetric(
                    group_name=group_name,
                    group_value=group_value,
                    count=len(entries),
                    avg_relevance=round(_avg([e["relevance"] for e in entries]), 4),
                    avg_completeness=round(_avg([e["completeness"] for e in entries]), 4),
                    avg_faithfulness=round(_avg([e["faithfulness"] for e in entries]), 4),
                    field_accuracy=round(field_acc, 4),
                )
            )

    detail = EvaluationRunDetail(
        id=run_id,
        name=name,
        timestamp=datetime.now(UTC),
        query_count=len(golden_examples),
        avg_latency_ms=round(_avg(latencies), 1),
        retrieval_metrics=RetrievalMetrics(
            precision_at_k={str(k): round(_avg(v), 4) for k, v in all_precisions.items()},
            recall_at_k={str(k): round(_avg(v), 4) for k, v in all_recalls.items()},
            mrr=round(_avg(all_mrrs), 4),
        ),
        generation_metrics=GenerationMetrics(
            faithfulness=round(_avg(all_faithfulness), 4),
            relevance=round(_avg(all_relevance), 4),
            completeness=round(_avg(all_completeness), 4),
        ),
        queries=queries_results,
        latency_per_query=latencies,
        cost_per_query=costs,
        per_field_metrics=per_field,
        stratified_metrics=stratified,
        judge_metrics=JudgeMetrics(
            avg_correctness=round(_avg(all_judge_correctness), 2),
            avg_completeness=round(_avg(all_judge_completeness), 2),
            avg_grounding=round(_avg(all_judge_grounding), 2),
        ),
        prompt_version=prompt_version,
        model_id=model_id,
        golden_dataset_version=dataset_version,
    )

    eval_store[run_id] = detail
    return detail


def run_comparison(version_a: str, version_b: str, name: str = "Prompt Comparison") -> dict:
    """Run the golden dataset against two prompt versions and return side-by-side results."""
    result_a = run_evaluation(name=f"{name} — {version_a}", prompt_version=version_a)
    result_b = run_evaluation(name=f"{name} — {version_b}", prompt_version=version_b)

    return {
        "version_a": {
            "prompt_version": result_a.prompt_version,
            "eval_id": result_a.id,
            "generation_metrics": result_a.generation_metrics.model_dump(),
            "retrieval_metrics": result_a.retrieval_metrics.model_dump(),
            "per_field_metrics": [m.model_dump() for m in result_a.per_field_metrics],
            "judge_metrics": result_a.judge_metrics.model_dump() if result_a.judge_metrics else None,
            "avg_latency_ms": result_a.avg_latency_ms,
        },
        "version_b": {
            "prompt_version": result_b.prompt_version,
            "eval_id": result_b.id,
            "generation_metrics": result_b.generation_metrics.model_dump(),
            "retrieval_metrics": result_b.retrieval_metrics.model_dump(),
            "per_field_metrics": [m.model_dump() for m in result_b.per_field_metrics],
            "judge_metrics": result_b.judge_metrics.model_dump() if result_b.judge_metrics else None,
            "avg_latency_ms": result_b.avg_latency_ms,
        },
        "regression_check": _check_regression(result_a, result_b),
    }


def _check_regression(baseline: EvaluationRunDetail, candidate: EvaluationRunDetail, tolerance: float = 0.05) -> dict:  # type: ignore[type-arg]
    """Compare candidate against baseline. Flag regressions beyond tolerance."""
    checks: dict = {}
    for metric_name in ("faithfulness", "relevance", "completeness"):
        base_val = getattr(baseline.generation_metrics, metric_name)
        cand_val = getattr(candidate.generation_metrics, metric_name)
        diff = cand_val - base_val
        checks[metric_name] = {
            "baseline": base_val,
            "candidate": cand_val,
            "diff": round(diff, 4),
            "regressed": diff < -tolerance,
        }

    # Per-field regression check
    base_fields = {m.field_name: m.accuracy for m in baseline.per_field_metrics}
    cand_fields = {m.field_name: m.accuracy for m in candidate.per_field_metrics}
    field_regressions = []
    for field, base_acc in base_fields.items():
        cand_acc = cand_fields.get(field, 0.0)
        if cand_acc < base_acc - tolerance:
            field_regressions.append(
                {
                    "field": field,
                    "baseline": base_acc,
                    "candidate": cand_acc,
                    "diff": round(cand_acc - base_acc, 4),
                }
            )

    checks["field_regressions"] = field_regressions
    checks["blocked"] = (
        any(c.get("regressed") for c in checks.values() if isinstance(c, dict) and "regressed" in c)
        or len(field_regressions) > 0
    )

    return checks


def get_evaluation_runs() -> list[EvaluationRun]:
    return [
        EvaluationRun(
            id=r.id,
            name=r.name,
            timestamp=r.timestamp,
            query_count=r.query_count,
            avg_latency_ms=r.avg_latency_ms,
            retrieval_metrics=r.retrieval_metrics,
            generation_metrics=r.generation_metrics,
        )
        for r in eval_store.values()
    ]


def get_evaluation_run(run_id: str) -> EvaluationRunDetail | None:
    return eval_store.get(run_id)
