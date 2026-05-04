import type { Document } from "@/types/document";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import { format } from "date-fns";

interface Props {
  documents: Document[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

const statusVariant: Record<string, "default" | "secondary" | "destructive"> = {
  ready: "default",
  processing: "secondary",
  error: "destructive",
};

export function DocumentList({ documents, selectedId, onSelect, onDelete }: Props) {
  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-muted-foreground">
        No documents uploaded yet
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Chunks</TableHead>
          <TableHead>Uploaded</TableHead>
          <TableHead className="w-10" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {documents.map((doc) => (
          <TableRow
            key={doc.id}
            onClick={() => onSelect(doc.id)}
            className={`cursor-pointer ${selectedId === doc.id ? "bg-accent" : ""}`}
          >
            <TableCell className="font-medium">{doc.name}</TableCell>
            <TableCell>
              <Badge variant={statusVariant[doc.status] ?? "secondary"}>
                {doc.status}
              </Badge>
            </TableCell>
            <TableCell className="text-right font-mono">{doc.chunk_count}</TableCell>
            <TableCell className="text-muted-foreground">
              {format(new Date(doc.upload_date), "MMM d, yyyy HH:mm")}
            </TableCell>
            <TableCell>
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => { e.stopPropagation(); onDelete(doc.id); }}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
