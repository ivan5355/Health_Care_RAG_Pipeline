import { useMemo, type ReactNode } from "react";
import type { SourceChunk } from "@/types/chat";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const STOP_WORDS = new Set([
  "the", "a", "an", "is", "was", "were", "are", "be", "been", "being",
  "have", "has", "had", "do", "does", "did", "will", "would", "shall",
  "should", "may", "might", "must", "can", "could", "of", "in", "to",
  "for", "with", "on", "at", "from", "by", "as", "or", "and", "but",
  "if", "not", "no", "so", "up", "out", "about", "into", "through",
  "what", "which", "who", "whom", "this", "that", "these", "those",
  "how", "when", "where", "why", "all", "each", "every", "both",
]);

function extractKeywords(question: string): string[] {
  return question
    .toLowerCase()
    .replace(/[?.,!'"]/g, "")
    .split(/\s+/)
    .filter((w) => w.length > 2 && !STOP_WORDS.has(w));
}

function highlightText(text: string, keywords: string[]): ReactNode[] {
  if (keywords.length === 0) return [text];

  const pattern = new RegExp(`(${keywords.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "gi");
  const parts = text.split(pattern);

  return parts.map((part, i) => {
    if (keywords.some((k) => part.toLowerCase() === k.toLowerCase())) {
      return (
        <mark key={i} className="bg-yellow-200 dark:bg-yellow-800 rounded-sm px-0.5">
          {part}
        </mark>
      );
    }
    return part;
  });
}

interface Props {
  source: SourceChunk;
  rank: number;
  highlighted?: boolean;
  query?: string;
}

export function SourceChunkCard({ source, rank, highlighted, query }: Props) {
  const keywords = useMemo(() => (query ? extractKeywords(query) : []), [query]);
  const highlightedContent = useMemo(() => highlightText(source.text, keywords), [source.text, keywords]);

  return (
    <Card
      id={`source-${rank}`}
      className={`transition-all ${highlighted ? "ring-2 ring-primary" : ""}`}
    >
      <CardHeader className="py-3 px-4 flex flex-row items-center gap-2">
        <span className="flex items-center justify-center h-6 w-6 text-xs font-bold bg-primary text-primary-foreground rounded-full">
          {rank}
        </span>
        <Badge variant="outline" className="text-xs">
          {source.section_name}
        </Badge>
        <span className="text-xs text-muted-foreground ml-auto">
          {source.document_name}
        </span>
      </CardHeader>
      <CardContent className="px-4 pb-3 space-y-2">
        <pre className="text-xs whitespace-pre-wrap font-mono bg-muted p-2 rounded max-h-32 overflow-auto">
          {highlightedContent}
        </pre>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Similarity</span>
          <Progress value={source.similarity_score * 100} className="h-1.5 flex-1" />
          <span className="text-xs font-mono">
            {(source.similarity_score * 100).toFixed(1)}%
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
