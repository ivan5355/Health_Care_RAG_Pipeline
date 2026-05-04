import { useRef, useEffect, useState, useCallback } from "react";
import { useChat } from "@/hooks/useChat";
import { useDocuments } from "@/hooks/useDocuments";
import { ChatInput } from "./ChatInput";
import { ChatMessage } from "./ChatMessage";
import { SuggestedQuestions } from "./SuggestedQuestions";
import { DocumentSelector } from "./DocumentSelector";
import { Loader2 } from "lucide-react";

export function ChatPage() {
  const { messages, loading, sendMessage } = useChat();
  const { documents } = useDocuments();
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleSend = useCallback(
    (message: string) => {
      sendMessage(message, selectedDocumentIds.length > 0 ? selectedDocumentIds : undefined);
    },
    [sendMessage, selectedDocumentIds]
  );

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <div className="border-b px-6 py-4">
        <h1 className="text-lg font-semibold">Chat</h1>
        <p className="text-sm text-muted-foreground">
          Ask questions about uploaded healthcare documents
        </p>
        <DocumentSelector
          documents={documents}
          selectedIds={selectedDocumentIds}
          onSelectionChange={setSelectedDocumentIds}
        />
      </div>

      <div ref={scrollRef} className="flex-1 overflow-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <SuggestedQuestions onSelect={handleSend} />
        ) : (
          messages.map((msg, idx) => {
            let query: string | undefined;
            if (msg.role === "assistant" && idx > 0 && messages[idx - 1].role === "user") {
              query = messages[idx - 1].content;
            }
            return <ChatMessage key={msg.id} message={msg} query={query} />;
          })
        )}
        {loading && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Retrieving and generating answer...</span>
          </div>
        )}
      </div>

      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  );
}
