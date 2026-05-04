import type { EvaluationRun } from "@/types/evaluation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  run: EvaluationRun;
}

function MetricCard({ label, value, format = "percent" }: { label: string; value: number; format?: "percent" | "ms" }) {
  const display = format === "percent" ? `${(value * 100).toFixed(1)}%` : `${value.toFixed(0)}ms`;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{display}</p>
      </CardContent>
    </Card>
  );
}

export function MetricsOverview({ run }: Props) {
  const { retrieval_metrics: r, generation_metrics: g } = run;
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <MetricCard label="Precision@5" value={r.precision_at_k["5"] ?? 0} />
      <MetricCard label="Recall@5" value={r.recall_at_k["5"] ?? 0} />
      <MetricCard label="MRR" value={r.mrr} />
      <MetricCard label="Avg Latency" value={run.avg_latency_ms} format="ms" />
      <MetricCard label="Faithfulness" value={g.faithfulness} />
      <MetricCard label="Relevance" value={g.relevance} />
      <MetricCard label="Completeness" value={g.completeness} />
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Queries</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{run.query_count}</p>
        </CardContent>
      </Card>
    </div>
  );
}
