export interface SourceChunk {
  chunk_id: string;
  document_name: string;
  section_name: string;
  text: string;
  similarity_score: number;
  chunk_index: number;
  patient_name: string;
}

export interface QueryMetadata {
  retrieval_latency_ms: number;
  generation_latency_ms: number;
  total_latency_ms: number;
  total_tokens: number;
  model: string;
  prompt_version?: string;
}

export interface RAGResponse {
  answer: string;
  sources: SourceChunk[];
  metadata: QueryMetadata;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
  metadata?: QueryMetadata;
  timestamp: Date;
}
