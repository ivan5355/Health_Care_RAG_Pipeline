import { useState, useEffect, useCallback } from "react";
import type { EvaluationRun, EvaluationRunDetail } from "@/types/evaluation";
import { getEvaluations, getEvaluationById, runEvaluation } from "@/services/api";

export function useEvaluations() {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const fetchRuns = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getEvaluations();
      setRuns(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  const triggerRun = useCallback(async () => {
    setRunning(true);
    try {
      await runEvaluation();
      await fetchRuns();
    } finally {
      setRunning(false);
    }
  }, [fetchRuns]);

  return { runs, loading, running, triggerRun, refresh: fetchRuns };
}

export function useEvaluationDetail(id: string | null) {
  const [detail, setDetail] = useState<EvaluationRunDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) {
      setDetail(null);
      return;
    }
    setLoading(true);
    getEvaluationById(id)
      .then(setDetail)
      .finally(() => setLoading(false));
  }, [id]);

  return { detail, loading };
}
