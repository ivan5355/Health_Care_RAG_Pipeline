import type { EvaluationRunDetail } from "@/types/evaluation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface Props {
  detail: EvaluationRunDetail;
}

export function LatencyCostChart({ detail }: Props) {
  const data = detail.latency_per_query.map((latency, i) => ({
    query: `Q${i + 1}`,
    latency,
    cost: detail.cost_per_query[i] * 1000,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Latency & Cost per Query</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data}>
            <XAxis dataKey="query" fontSize={12} />
            <YAxis yAxisId="latency" fontSize={12} tickFormatter={(v: number) => `${v}ms`} />
            <YAxis yAxisId="cost" orientation="right" fontSize={12} tickFormatter={(v: number) => `$${v.toFixed(1)}`} />
            <Tooltip />
            <Legend />
            <Line yAxisId="latency" type="monotone" dataKey="latency" stroke="hsl(220, 70%, 50%)" name="Latency (ms)" />
            <Line yAxisId="cost" type="monotone" dataKey="cost" stroke="hsl(30, 80%, 55%)" name="Cost (x1000)" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
