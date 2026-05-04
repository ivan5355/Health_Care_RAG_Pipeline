import { useState } from "react";
import { useDocuments, useDocumentDetail } from "@/hooks/useDocuments";
import { DocumentUploadZone } from "./DocumentUploadZone";
import { DocumentList } from "./DocumentList";
import { DocumentPreview } from "./DocumentPreview";
import { Separator } from "@/components/ui/separator";

export function DocumentsPage() {
  const { documents, upload, remove } = useDocuments();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { document: selectedDoc, loading: detailLoading } = useDocumentDetail(selectedId);

  return (
    <div className="flex h-full">
      <div className="flex-1 border-r overflow-auto">
        <div className="px-6 py-4 border-b">
          <h1 className="text-lg font-semibold">Documents</h1>
          <p className="text-sm text-muted-foreground">
            Upload and manage healthcare documents
          </p>
        </div>
        <div className="p-6 space-y-6">
          <DocumentUploadZone onUpload={async (file) => { await upload(file); }} />
          <Separator />
          <DocumentList
            documents={documents}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onDelete={remove}
          />
        </div>
      </div>
      <div className="w-[480px] overflow-auto p-6">
        <DocumentPreview document={selectedDoc} loading={detailLoading} />
      </div>
    </div>
  );
}
