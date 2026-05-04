import type { GenerationMetrics } from "@/types/evaluation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";

interface Props {
  metrics: GenerationMetrics;
}

export function GenerationMetricsChart({ metrics }: Props) {
  const data = [
    { metric: "Faithfulness", value: metrics.faithfulness },
    { metric: "Relevance", value: metrics.relevance },
    { metric: "Completeness", value: metrics.completeness },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Generation Quality</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <RadarChart data={data}>
            <PolarGrid />
            <PolarAngleAxis dataKey="metric" fontSize={12} />
            <PolarRadiusAxis domain={[0, 1]} fontSize={10} tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`} />
            <Radar dataKey="value" stroke="hsl(260, 60%, 50%)" fill="hsl(260, 60%, 50%)" fillOpacity={0.3} />
          </RadarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
