import type { ReactNode } from "react";

interface CitationSegment {
  type: "text" | "citation";
  content: string;
  index?: number;
}

export function parseCitations(text: string): CitationSegment[] {
  const segments: CitationSegment[] = [];
  const regex = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: "text", content: text.slice(lastIndex, match.index) });
    }
    segments.push({ type: "citation", content: match[0], index: parseInt(match[1]) });
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    segments.push({ type: "text", content: text.slice(lastIndex) });
  }

  return segments;
}

export function renderCitations(
  text: string,
  onCitationClick?: (index: number) => void
): ReactNode[] {
  const segments = parseCitations(text);
  return segments.map((seg, i) => {
    if (seg.type === "citation" && seg.index !== undefined) {
      return (
        <button
          key={i}
          onClick={() => onCitationClick?.(seg.index!)}
          className="inline-flex items-center justify-center h-5 min-w-5 px-1 text-xs font-medium bg-primary text-primary-foreground rounded-full hover:bg-primary/80 cursor-pointer mx-0.5"
        >
          {seg.index}
        </button>
      );
    }
    return <span key={i}>{seg.content}</span>;
  });
}
