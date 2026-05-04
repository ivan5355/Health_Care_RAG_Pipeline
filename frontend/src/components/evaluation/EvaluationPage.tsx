import { useEvaluations, useEvaluationDetail } from "@/hooks/useEvaluation";
import { MetricsOverview } from "./MetricsOverview";
import { RetrievalMetricsChart } from "./RetrievalMetricsChart";
import { GenerationMetricsChart } from "./GenerationMetricsChart";
import { LatencyCostChart } from "./LatencyCostChart";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Play, Loader2 } from "lucide-react";

export function EvaluationPage() {
  const { runs, loading: runsLoading, running, triggerRun } = useEvaluations();
  const latestRunId = runs.length > 0 ? runs[0].id : null;
  const { detail } = useEvaluationDetail(latestRunId);

  if (runsLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      </div>
    );
  }

  const latestRun = runs[0];

  return (
    <div className="overflow-auto">
      <div className="px-6 py-4 border-b flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Evaluation Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Run the RAG pipeline against ground-truth questions and measure real metrics
          </p>
        </div>
        <Button onClick={triggerRun} disabled={running}>
          {running ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Running evaluation...
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" />
              Run Evaluation
            </>
          )}
        </Button>
      </div>

      <div className="p-6 space-y-6">
        {latestRun ? (
          <>
            <div>
              <h2 className="text-sm font-medium mb-3">
                {latestRun.name}
                <span className="text-xs text-muted-foreground ml-2">
                  ({latestRun.query_count} queries)
                </span>
              </h2>
              <MetricsOverview run={latestRun} />
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <RetrievalMetricsChart metrics={latestRun.retrieval_metrics} />
              <GenerationMetricsChart metrics={latestRun.generation_metrics} />
            </div>

            {detail && <LatencyCostChart detail={detail} />}
          </>
        ) : (
          <div className="text-center py-16 text-muted-foreground">
            <p className="text-sm">No evaluation runs yet</p>
            <p className="text-xs mt-1">
              Click "Run Evaluation" to test the RAG pipeline against 5 ground-truth questions
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
