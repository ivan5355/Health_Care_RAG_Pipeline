import { login, queryRAG } from "../api";

const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

describe("API service", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.stubGlobal("localStorage", localStorageMock);
    localStorageMock.clear();
  });

  describe("login", () => {
    it("sends correct payload to login endpoint", async () => {
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({ access_token: "tok123", token_type: "bearer", role: "admin" }),
      };
      vi.mocked(fetch).mockResolvedValue(mockResponse as Response);

      const result = await login("admin", "admin");

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/auth/login"),
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: "admin", password: "admin" }),
        })
      );
      expect(result.access_token).toBe("tok123");
    });

    it("throws on invalid credentials", async () => {
      const mockResponse = { ok: false, status: 401, statusText: "Unauthorized" };
      vi.mocked(fetch).mockResolvedValue(mockResponse as Response);

      await expect(login("admin", "wrong")).rejects.toThrow("Invalid credentials");
    });
  });

  describe("queryRAG", () => {
    it("sends correct body with auth header", async () => {
      localStorage.setItem("auth_token", "my-token");

      const mockResponse = {
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            answer: "The total is $687",
            sources: [],
            metadata: { total_tokens: 100 },
          }),
      };
      vi.mocked(fetch).mockResolvedValue(mockResponse as Response);

      await queryRAG("What is the total?", 5, ["doc1"]);

      const [url, options] = vi.mocked(fetch).mock.calls[0];
      expect(url).toContain("/query");
      expect(options?.method).toBe("POST");

      const headers = options?.headers as Headers;
      expect(headers.get("Authorization")).toBe("Bearer my-token");

      const body = JSON.parse(options?.body as string);
      expect(body.question).toBe("What is the total?");
      expect(body.top_k).toBe(5);
      expect(body.document_ids).toEqual(["doc1"]);
    });
  });

  describe("401 handling", () => {
    it("clears token and redirects on 401", async () => {
      localStorage.setItem("auth_token", "expired-token");

      const mockResponse = { ok: false, status: 401, statusText: "Unauthorized" };
      vi.mocked(fetch).mockResolvedValue(mockResponse as Response);

      // Mock window.location
      const locationMock = { href: "" };
      Object.defineProperty(window, "location", { value: locationMock, writable: true });

      await expect(queryRAG("test")).rejects.toThrow();
      expect(localStorage.getItem("auth_token")).toBeNull();
      expect(locationMock.href).toBe("/login");
    });
  });
});
