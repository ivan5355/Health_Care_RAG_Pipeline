import type { RetrievalMetrics } from "@/types/evaluation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface Props {
  metrics: RetrievalMetrics;
}

export function RetrievalMetricsChart({ metrics }: Props) {
  const ks = Object.keys(metrics.precision_at_k).sort((a, b) => Number(a) - Number(b));
  const data = ks.map((k) => ({
    name: `K=${k}`,
    Precision: metrics.precision_at_k[k],
    Recall: metrics.recall_at_k[k],
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Retrieval: Precision & Recall @ K</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <XAxis dataKey="name" fontSize={12} />
            <YAxis domain={[0, 1]} fontSize={12} tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`} />
            <Tooltip formatter={(v) => `${(Number(v) * 100).toFixed(1)}%`} />
            <Legend />
            <Bar dataKey="Precision" fill="hsl(220, 70%, 50%)" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Recall" fill="hsl(150, 60%, 45%)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
