import { parseCitations } from "../citationParser";

describe("parseCitations", () => {
  it("returns single text segment when no citations present", () => {
    const result = parseCitations("Hello world");
    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({ type: "text", content: "Hello world" });
  });

  it("parses a single citation", () => {
    const result = parseCitations("See [1] for details");
    expect(result).toHaveLength(3);
    expect(result[0]).toEqual({ type: "text", content: "See " });
    expect(result[1]).toEqual({ type: "citation", content: "[1]", index: 1 });
    expect(result[2]).toEqual({ type: "text", content: " for details" });
  });

  it("parses multiple citations", () => {
    const result = parseCitations("Sources [1] and [2] confirm this");
    const citations = result.filter((s) => s.type === "citation");
    expect(citations).toHaveLength(2);
    expect(citations[0].index).toBe(1);
    expect(citations[1].index).toBe(2);
  });

  it("handles adjacent citations", () => {
    const result = parseCitations("[1][2]");
    const citations = result.filter((s) => s.type === "citation");
    expect(citations).toHaveLength(2);
  });

  it("returns empty array for empty string", () => {
    const result = parseCitations("");
    expect(result).toHaveLength(0);
  });

  it("handles text with no surrounding spaces around citation", () => {
    const result = parseCitations("total[1]billed");
    expect(result).toHaveLength(3);
    expect(result[0]).toEqual({ type: "text", content: "total" });
    expect(result[1]).toEqual({ type: "citation", content: "[1]", index: 1 });
    expect(result[2]).toEqual({ type: "text", content: "billed" });
  });
});
