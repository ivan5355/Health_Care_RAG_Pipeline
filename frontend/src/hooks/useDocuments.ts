import { useState, useEffect, useCallback } from "react";
import type { Document, DocumentDetail } from "@/types/document";
import { getDocuments, uploadDocument, getDocumentById, deleteDocument } from "@/services/api";

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      setLoading(true);
      const res = await getDocuments();
      setDocuments(res.documents);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch documents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const upload = async (file: File): Promise<DocumentDetail> => {
    const doc = await uploadDocument(file);
    await fetchDocuments();
    return doc;
  };

  const remove = async (id: string) => {
    await deleteDocument(id);
    await fetchDocuments();
  };

  return { documents, loading, error, upload, remove, refresh: fetchDocuments };
}

export function useDocumentDetail(id: string | null) {
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) {
      setDocument(null);
      return;
    }
    setLoading(true);
    getDocumentById(id)
      .then(setDocument)
      .finally(() => setLoading(false));
  }, [id]);

  return { document, loading };
}
