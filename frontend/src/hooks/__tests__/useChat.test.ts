import { renderHook, act, waitFor } from "@testing-library/react";
import type { RAGResponse } from "@/types/chat";
import { useChat } from "../useChat";

vi.mock("@/services/api", () => ({
  queryRAG: vi.fn(),
}));

import { queryRAG } from "@/services/api";

describe("useChat", () => {
  beforeEach(() => {
    vi.mocked(queryRAG).mockReset();
  });

  it("starts with empty messages and not loading", () => {
    const { result } = renderHook(() => useChat());
    expect(result.current.messages).toHaveLength(0);
    expect(result.current.loading).toBe(false);
  });

  it("adds user and assistant messages after sendMessage", async () => {
    vi.mocked(queryRAG).mockResolvedValue({
      answer: "The total is $687.00",
      sources: [],
      metadata: {
        retrieval_latency_ms: 10,
        generation_latency_ms: 100,
        total_latency_ms: 110,
        total_tokens: 150,
        model: "claude",
        prompt_version: "v1",
      },
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("What is the total?");
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].content).toBe("What is the total?");
    expect(result.current.messages[1].role).toBe("assistant");
    expect(result.current.messages[1].content).toBe("The total is $687.00");
  });

  it("sets loading during request", async () => {
    let resolveQuery: (value: RAGResponse) => void;
    vi.mocked(queryRAG).mockImplementation(
      () => new Promise<RAGResponse>((resolve) => { resolveQuery = resolve; })
    );

    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage("test");
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(true);
    });

    await act(async () => {
      resolveQuery!({
        answer: "answer",
        sources: [],
        metadata: { retrieval_latency_ms: 0, generation_latency_ms: 0, total_latency_ms: 0, total_tokens: 0, model: "", prompt_version: "" },
      });
    });

    expect(result.current.loading).toBe(false);
  });

  it("handles API errors gracefully", async () => {
    vi.mocked(queryRAG).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("test question");
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[1].role).toBe("assistant");
    expect(result.current.messages[1].content).toContain("Error");
    expect(result.current.loading).toBe(false);
  });

  it("clearMessages resets to empty", async () => {
    vi.mocked(queryRAG).mockResolvedValue({
      answer: "test",
      sources: [],
      metadata: { retrieval_latency_ms: 0, generation_latency_ms: 0, total_latency_ms: 0, total_tokens: 0, model: "", prompt_version: "" },
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("hello");
    });

    expect(result.current.messages.length).toBeGreaterThan(0);

    act(() => {
      result.current.clearMessages();
    });

    expect(result.current.messages).toHaveLength(0);
  });
});
