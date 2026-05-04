import { useState, useMemo } from "react";
import type { DocumentDetail } from "@/types/document";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

interface Props {
  document: DocumentDetail;
}

interface ServiceLine {
  dos: string;
  cpt: string;
  modifier: string;
  description: string;
  billed: string;
  allowed: string;
  copay: string;
  paid: string;
}

type SortKey = keyof ServiceLine;
type SortDir = "asc" | "desc";

function parseServiceLines(chunk: string): ServiceLine[] {
  const lines = chunk.split("\n").filter((l) => l.trim());
  const result: ServiceLine[] = [];
  for (const line of lines) {
    const match = line.match(
      /(\d{2}\/\d{2}\/\d{4})\s+(\d{5})\s+(\S*)?\s+([\w\s/.-]+?)\s+\$\s*([\d,.]+)\s+\$\s*([\d,.]+)\s+\$\s*([\d,.]+)\s+\$\s*([\d,.]+)/
    );
    if (match) {
      result.push({
        dos: match[1],
        cpt: match[2],
        modifier: match[3] || "",
        description: match[4].trim(),
        billed: match[5],
        allowed: match[6],
        copay: match[7],
        paid: match[8],
      });
    }
  }
  return result;
}

function parseDiagnosisCodes(chunk: string): { code: string; description: string }[] {
  const lines = chunk.split("\n").filter((l) => l.trim());
  const result: { code: string; description: string }[] = [];
  for (const line of lines) {
    const match = line.match(/\d+\.\s+(\S+)\s+-\s+(.+)/);
    if (match) {
      result.push({ code: match[1], description: match[2].trim() });
    }
  }
  return result;
}

function parseKeyValuePairs(chunk: string): { field: string; value: string }[] {
  const pairs: { field: string; value: string }[] = [];
  const lines = chunk.split("\n").filter((l) => l.trim());
  for (const line of lines) {
    const kvMatch = line.match(/^\s*(.+?):\s+(.+?)(?:\s{2,}|$)/);
    if (kvMatch) {
      const remaining = line.slice(kvMatch[0].length);
      pairs.push({ field: kvMatch[1].trim(), value: kvMatch[2].trim() });
      const secondKv = remaining.match(/(.+?):\s+(.+)/);
      if (secondKv) {
        pairs.push({ field: secondKv[1].trim(), value: secondKv[2].trim() });
      }
    }
  }
  return pairs;
}

function SortableHeader({
  label,
  sortKey,
  currentKey,
  currentDir,
  onSort,
}: {
  label: string;
  sortKey: SortKey;
  currentKey: SortKey | null;
  currentDir: SortDir;
  onSort: (key: SortKey) => void;
}) {
  return (
    <TableHead
      onClick={() => onSort(sortKey)}
      className="cursor-pointer select-none hover:bg-accent/50 transition-colors"
    >
      <span className="flex items-center gap-1">
        {label}
        {currentKey === sortKey ? (
          currentDir === "asc" ? <ArrowUp className="h-3 w-3 text-foreground" /> : <ArrowDown className="h-3 w-3 text-foreground" />
        ) : (
          <ArrowUpDown className="h-3 w-3 text-muted-foreground/40" />
        )}
      </span>
    </TableHead>
  );
}

export function ExtractedFieldsTable({ document }: Props) {
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const serviceChunk = document.chunks.find((c) => c.section_name === "SERVICE LINES");
  const diagnosisChunk = document.chunks.find((c) => c.section_name === "DIAGNOSIS CODES");
  const patientChunk = document.chunks.find((c) => c.section_name === "PATIENT INFORMATION");
  const providerChunk = document.chunks.find((c) => c.section_name === "PROVIDER INFORMATION");
  const totalsChunk = document.chunks.find((c) => c.section_name === "TOTALS");
  const headerChunk = document.chunks.find((c) => c.section_name === "Header");

  const serviceLines = useMemo(
    () => (serviceChunk ? parseServiceLines(serviceChunk.text) : []),
    [serviceChunk]
  );

  const sortedLines = useMemo(() => {
    if (!sortKey) return serviceLines;
    return [...serviceLines].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      const aNum = parseFloat(aVal.replace(/,/g, ""));
      const bNum = parseFloat(bVal.replace(/,/g, ""));
      if (!isNaN(aNum) && !isNaN(bNum)) {
        return sortDir === "asc" ? aNum - bNum : bNum - aNum;
      }
      return sortDir === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
  }, [serviceLines, sortKey, sortDir]);

  const diagnosisCodes = useMemo(
    () => (diagnosisChunk ? parseDiagnosisCodes(diagnosisChunk.text) : []),
    [diagnosisChunk]
  );

  const claimInfo = useMemo(
    () => (headerChunk ? parseKeyValuePairs(headerChunk.text) : []),
    [headerChunk]
  );
  const patientInfo = useMemo(
    () => (patientChunk ? parseKeyValuePairs(patientChunk.text) : []),
    [patientChunk]
  );
  const providerInfo = useMemo(
    () => (providerChunk ? parseKeyValuePairs(providerChunk.text) : []),
    [providerChunk]
  );
  const totalsInfo = useMemo(
    () => (totalsChunk ? parseKeyValuePairs(totalsChunk.text) : []),
    [totalsChunk]
  );

  return (
    <Tabs defaultValue="service-lines">
      <TabsList>
        <TabsTrigger value="service-lines">Service Lines</TabsTrigger>
        <TabsTrigger value="diagnosis">Diagnosis Codes</TabsTrigger>
        <TabsTrigger value="details">Claim Details</TabsTrigger>
      </TabsList>

      <TabsContent value="service-lines">
        {sortedLines.length > 0 ? (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <SortableHeader label="DOS" sortKey="dos" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
                  <SortableHeader label="CPT" sortKey="cpt" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
                  <TableHead>Mod</TableHead>
                  <SortableHeader label="Description" sortKey="description" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
                  <SortableHeader label="Billed" sortKey="billed" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
                  <SortableHeader label="Allowed" sortKey="allowed" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
                  <SortableHeader label="Copay" sortKey="copay" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
                  <SortableHeader label="Paid" sortKey="paid" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedLines.map((line, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-mono text-xs">{line.dos}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-xs">{line.cpt}</Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{line.modifier || "—"}</TableCell>
                    <TableCell className="text-xs">{line.description}</TableCell>
                    <TableCell className="text-right font-mono text-xs">${line.billed}</TableCell>
                    <TableCell className="text-right font-mono text-xs">${line.allowed}</TableCell>
                    <TableCell className="text-right font-mono text-xs">${line.copay}</TableCell>
                    <TableCell className="text-right font-mono text-xs font-medium">${line.paid}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground py-4">No service lines found</p>
        )}
      </TabsContent>

      <TabsContent value="diagnosis">
        {diagnosisCodes.length > 0 ? (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ICD-10 Code</TableHead>
                  <TableHead>Description</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {diagnosisCodes.map((dx, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-xs">{dx.code}</Badge>
                    </TableCell>
                    <TableCell className="text-sm">{dx.description}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground py-4">No diagnosis codes found</p>
        )}
      </TabsContent>

      <TabsContent value="details" className="space-y-4">
        {[
          { title: "Claim", pairs: claimInfo },
          { title: "Patient", pairs: patientInfo },
          { title: "Provider", pairs: providerInfo },
          { title: "Totals", pairs: totalsInfo },
        ]
          .filter((s) => s.pairs.length > 0)
          .map((section) => (
            <div key={section.title}>
              <h4 className="text-xs font-medium text-muted-foreground uppercase mb-2">
                {section.title}
              </h4>
              <div className="rounded-md border">
                <Table>
                  <TableBody>
                    {section.pairs.map((p, i) => (
                      <TableRow key={i}>
                        <TableCell className="text-xs text-muted-foreground w-40">{p.field}</TableCell>
                        <TableCell className="text-sm font-medium">{p.value}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          ))}
      </TabsContent>
    </Tabs>
  );
}
