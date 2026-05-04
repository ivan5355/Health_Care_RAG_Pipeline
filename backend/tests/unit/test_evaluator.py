from services.evaluator import (
    _check_regression,
    check_completeness,
    check_faithfulness,
    check_relevance,
    compute_mrr,
    compute_per_field_accuracy,
    compute_precision_at_k,
    compute_recall_at_k,
)

# --- Precision ---


def test_precision_all_relevant():
    assert compute_precision_at_k(["TOTALS", "SERVICE LINES"], ["TOTALS", "SERVICE LINES"], k=2) == 1.0


def test_precision_none_relevant():
    assert compute_precision_at_k(["REMARKS"], ["TOTALS"], k=1) == 0.0


def test_precision_partial():
    result = compute_precision_at_k(["TOTALS", "REMARKS", "DIAGNOSIS CODES"], ["TOTALS", "DIAGNOSIS CODES"], k=3)
    assert abs(result - 2 / 3) < 0.01


def test_precision_case_insensitive():
    assert compute_precision_at_k(["totals"], ["TOTALS"], k=1) == 1.0


def test_precision_empty_retrieved():
    assert compute_precision_at_k([], ["TOTALS"], k=1) == 0.0


# --- Recall ---


def test_recall_full():
    assert compute_recall_at_k(["TOTALS", "SERVICE LINES", "OTHER"], ["TOTALS", "SERVICE LINES"], k=5) == 1.0


def test_recall_partial():
    result = compute_recall_at_k(["TOTALS"], ["TOTALS", "SERVICE LINES"], k=5)
    assert result == 0.5


def test_recall_empty_relevant():
    assert compute_recall_at_k(["TOTALS"], [], k=5) == 0.0


# --- MRR ---


def test_mrr_first_match():
    assert compute_mrr(["TOTALS", "REMARKS"], ["TOTALS"]) == 1.0


def test_mrr_second_match():
    assert compute_mrr(["REMARKS", "TOTALS"], ["TOTALS"]) == 0.5


def test_mrr_no_match():
    assert compute_mrr(["REMARKS", "OTHER"], ["TOTALS"]) == 0.0


# --- Faithfulness ---


def test_faithfulness_fully_grounded():
    answer = "The total billed amount was $687.00"
    sources = ["Total Billed: $687.00 Total Allowed: $485.00"]
    result = check_faithfulness(answer, sources)
    assert result > 0.5


def test_faithfulness_hallucinated():
    answer = "The patient underwent cardiac surgery requiring hospitalization"
    sources = ["Total Billed: $687.00"]
    result = check_faithfulness(answer, sources)
    assert result < 0.5


# --- Relevance ---


def test_relevance_all_keywords_present():
    answer = "The total billed was $687.00"
    expected = "$687.00"
    result = check_relevance(answer, expected)
    assert result == 1.0


def test_relevance_no_keywords():
    answer = "I don't have that information"
    expected = "$687.00, $485.00"
    result = check_relevance(answer, expected)
    assert result == 0.0


# --- Completeness ---


def test_completeness_all_values():
    answer = "The codes are E11.9, I10"
    expected = "E11.9, I10"
    result = check_completeness(answer, expected)
    assert result == 1.0


def test_completeness_partial():
    answer = "The code is E11.9"
    expected = "E11.9, I10, J45.0"
    result = check_completeness(answer, expected)
    assert abs(result - 1 / 3) < 0.01


# --- Per-field accuracy ---


def test_per_field_accuracy_mixed():
    answer = "Total billed $687.00, member XYZ123456"
    fields = {"total_billed": "$687.00", "member_id": "XYZ123456", "copay": "$30.00"}
    result = compute_per_field_accuracy(answer, fields)
    assert result["total_billed"] is True
    assert result["member_id"] is True
    assert result["copay"] is False


# --- Regression check ---


def test_regression_not_blocked():
    from unittest.mock import MagicMock

    baseline = MagicMock()
    baseline.generation_metrics.faithfulness = 0.8
    baseline.generation_metrics.relevance = 0.7
    baseline.generation_metrics.completeness = 0.9
    baseline.per_field_metrics = []

    candidate = MagicMock()
    candidate.generation_metrics.faithfulness = 0.82
    candidate.generation_metrics.relevance = 0.72
    candidate.generation_metrics.completeness = 0.91
    candidate.per_field_metrics = []

    result = _check_regression(baseline, candidate)
    assert result["blocked"] is False


def test_regression_blocked():
    from unittest.mock import MagicMock

    baseline = MagicMock()
    baseline.generation_metrics.faithfulness = 0.8
    baseline.generation_metrics.relevance = 0.7
    baseline.generation_metrics.completeness = 0.9
    baseline.per_field_metrics = []

    candidate = MagicMock()
    candidate.generation_metrics.faithfulness = 0.7  # dropped 0.1 > tolerance 0.05
    candidate.generation_metrics.relevance = 0.7
    candidate.generation_metrics.completeness = 0.9
    candidate.per_field_metrics = []

    result = _check_regression(baseline, candidate)
    assert result["blocked"] is True
    assert result["faithfulness"]["regressed"] is True


def test_regression_within_tolerance():
    from unittest.mock import MagicMock

    baseline = MagicMock()
    baseline.generation_metrics.faithfulness = 0.8
    baseline.generation_metrics.relevance = 0.7
    baseline.generation_metrics.completeness = 0.9
    baseline.per_field_metrics = []

    candidate = MagicMock()
    candidate.generation_metrics.faithfulness = 0.77  # dropped 0.03, within 0.05 tolerance
    candidate.generation_metrics.relevance = 0.68  # dropped 0.02
    candidate.generation_metrics.completeness = 0.87  # dropped 0.03
    candidate.per_field_metrics = []

    result = _check_regression(baseline, candidate)
    assert result["blocked"] is False
