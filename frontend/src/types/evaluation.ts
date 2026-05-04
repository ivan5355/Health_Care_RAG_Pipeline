export interface RetrievalMetrics {
  precision_at_k: Record<string, number>;
  recall_at_k: Record<string, number>;
  mrr: number;
}

export interface GenerationMetrics {
  faithfulness: number;
  relevance: number;
  completeness: number;
}

export interface EvaluationRun {
  id: string;
  name: string;
  timestamp: string;
  query_count: number;
  avg_latency_ms: number;
  retrieval_metrics: RetrievalMetrics;
  generation_metrics: GenerationMetrics;
}

export interface EvaluationRunDetail extends EvaluationRun {
  queries: { question: string; expected: string }[];
  latency_per_query: number[];
  cost_per_query: number[];
}

