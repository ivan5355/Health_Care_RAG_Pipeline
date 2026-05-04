import type { DocumentListResponse, DocumentDetail } from "@/types/document";
import type { RAGResponse } from "@/types/chat";
import type { EvaluationRun, EvaluationRunDetail } from "@/types/evaluation";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("auth_token");
  const headers = new Headers(options?.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    window.location.href = "/login";
    throw new Error("Authentication required");
  }

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface AuthUser {
  username: string;
  role: "admin" | "viewer";
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: string;
}

export async function login(
  username: string,
  password: string
): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    throw new Error("Invalid credentials");
  }
  return res.json();
}

export async function getMe(): Promise<AuthUser> {
  return request("/auth/me");
}

export async function getDocuments(): Promise<DocumentListResponse> {
  return request("/documents");
}

export async function uploadDocument(file: File): Promise<DocumentDetail> {
  const formData = new FormData();
  formData.append("file", file);
  return request("/documents/upload", { method: "POST", body: formData });
}

export async function getDocumentById(id: string): Promise<DocumentDetail> {
  return request(`/documents/${id}`);
}

export async function deleteDocument(id: string): Promise<void> {
  await request(`/documents/${id}`, { method: "DELETE" });
}

export async function queryRAG(
  question: string,
  topK: number = 5,
  documentIds?: string[]
): Promise<RAGResponse> {
  return request("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      top_k: topK,
      document_ids: documentIds,
    }),
  });
}

export async function getEvaluations(): Promise<EvaluationRun[]> {
  return request("/evaluations");
}

export async function getEvaluationById(id: string): Promise<EvaluationRunDetail> {
  return request(`/evaluations/${id}`);
}

export async function runEvaluation(): Promise<EvaluationRunDetail> {
  return request("/evaluations/run", { method: "POST" });
}
