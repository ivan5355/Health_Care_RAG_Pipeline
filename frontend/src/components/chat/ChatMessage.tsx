import { useState } from "react";
import type { ChatMessage as ChatMessageType } from "@/types/chat";
import { renderCitations } from "@/lib/citationParser";
import { SourceChunkCard } from "./SourceChunkCard";
import { ChevronDown, ChevronUp, Clock, Coins } from "lucide-react";

interface Props {
  message: ChatMessageType;
  query?: string;
}

export function ChatMessage({ message, query }: Props) {
  const [highlightedSource, setHighlightedSource] = useState<number | null>(null);
  const [showSources, setShowSources] = useState(true);

  const handleCitationClick = (index: number) => {
    setHighlightedSource(index);
    setShowSources(true);
    document.getElementById(`source-${index}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="bg-primary text-primary-foreground px-4 py-2 rounded-2xl rounded-br-sm max-w-[70%]">
          <p className="text-sm">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="bg-muted px-4 py-3 rounded-2xl rounded-bl-sm max-w-[85%]">
        <div className="text-sm leading-relaxed whitespace-pre-wrap">
          {renderCitations(message.content, handleCitationClick)}
        </div>
      </div>

      {message.metadata && (
        <div className="flex gap-4 text-xs text-muted-foreground px-1">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {message.metadata.total_latency_ms.toFixed(0)}ms
          </span>
          <span className="flex items-center gap-1">
            <Coins className="h-3 w-3" />
            {message.metadata.total_tokens} tokens
          </span>
        </div>
      )}

      {message.sources && message.sources.length > 0 && (
        <div className="space-y-2">
          <button
            onClick={() => setShowSources(!showSources)}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {showSources ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            {message.sources.length} source{message.sources.length > 1 ? "s" : ""}
          </button>
          {showSources && (
            <div className="grid gap-2 max-w-[85%]">
              {message.sources.map((source, i) => (
                <SourceChunkCard
                  key={source.chunk_id}
                  source={source}
                  rank={i + 1}
                  highlighted={highlightedSource === i + 1}
                  query={query}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
