export interface DocumentChunk {
  id: string;
  document_id: string;
  section_name: string;
  text: string;
  chunk_index: number;
}

export interface Document {
  id: string;
  name: string;
  upload_date: string;
  status: "processing" | "ready" | "error";
  chunk_count: number;
  raw_text: string;
}

export interface DocumentDetail extends Document {
  chunks: DocumentChunk[];
}

export interface DocumentListResponse {
  documents: Document[];
}
