import type { DocumentDetail } from "@/types/document";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ExtractedFieldsTable } from "./ExtractedFieldsTable";

interface Props {
  document: DocumentDetail | null;
  loading: boolean;
}

export function DocumentPreview({ document, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!document) {
    return (
      <div className="text-center py-12 text-sm text-muted-foreground">
        Select a document to preview
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-semibold">{document.name}</h3>
        <p className="text-xs text-muted-foreground">
          {document.chunk_count} chunks (section-based)
        </p>
      </div>

      <Tabs defaultValue="fields">
        <TabsList>
          <TabsTrigger value="fields">Extracted Fields</TabsTrigger>
          <TabsTrigger value="raw">Raw Text</TabsTrigger>
          <TabsTrigger value="chunks">Chunks ({document.chunk_count})</TabsTrigger>
        </TabsList>
        <TabsContent value="fields">
          <ExtractedFieldsTable document={document} />
        </TabsContent>
        <TabsContent value="raw">
          <pre className="text-xs whitespace-pre-wrap font-mono bg-muted p-4 rounded-md max-h-[60vh] overflow-auto">
            {document.raw_text}
          </pre>
        </TabsContent>
        <TabsContent value="chunks" className="space-y-3">
          {document.chunks.map((chunk) => (
            <Card key={chunk.id}>
              <CardHeader className="py-2 px-4">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    {chunk.section_name}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    Chunk {chunk.chunk_index}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="px-4 pb-3">
                <pre className="text-xs whitespace-pre-wrap font-mono bg-muted p-2 rounded max-h-40 overflow-auto">
                  {chunk.text}
                </pre>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}
