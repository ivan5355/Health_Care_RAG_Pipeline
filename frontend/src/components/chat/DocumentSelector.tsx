import type { Document } from "@/types/document";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuSeparator,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { FileText, X, Filter } from "lucide-react";

interface Props {
  documents: Document[];
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
}

export function DocumentSelector({ documents, selectedIds, onSelectionChange }: Props) {
  const readyDocs = documents.filter((d) => d.status === "ready");

  const toggle = (id: string) => {
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((s) => s !== id));
    } else {
      onSelectionChange([...selectedIds, id]);
    }
  };

  const label =
    selectedIds.length === 0
      ? "All documents"
      : `${selectedIds.length} document${selectedIds.length > 1 ? "s" : ""} selected`;

  return (
    <div className="flex flex-wrap items-center gap-2 mt-2">
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Filter className="h-3.5 w-3.5" />
              {label}
            </Button>
          }
        />
        <DropdownMenuContent align="start">
          {readyDocs.length === 0 ? (
            <div className="px-2 py-1.5 text-xs text-muted-foreground">No documents uploaded</div>
          ) : (
            <>
              {selectedIds.length > 0 && (
                <>
                  <DropdownMenuItem onClick={() => onSelectionChange([])}>
                    Clear filter
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                </>
              )}
              {readyDocs.map((doc) => (
                <DropdownMenuCheckboxItem
                  key={doc.id}
                  checked={selectedIds.includes(doc.id)}
                  onCheckedChange={() => toggle(doc.id)}
                >
                  <FileText className="h-3.5 w-3.5 mr-1 shrink-0" />
                  <span className="truncate max-w-[200px]">{doc.name}</span>
                </DropdownMenuCheckboxItem>
              ))}
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {selectedIds.length > 0 &&
        selectedIds.map((id) => {
          const doc = readyDocs.find((d) => d.id === id);
          if (!doc) return null;
          return (
            <Badge key={id} variant="secondary" className="gap-1 text-xs">
              <span className="truncate max-w-[150px]">{doc.name}</span>
              <X
                className="h-3 w-3 cursor-pointer hover:text-destructive"
                onClick={() => onSelectionChange(selectedIds.filter((s) => s !== id))}
              />
            </Badge>
          );
        })}
    </div>
  );
}
