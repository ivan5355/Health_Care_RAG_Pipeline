import { cn } from "../utils";

describe("cn utility", () => {
  it("merges multiple classes", () => {
    const result = cn("px-2", "py-3");
    expect(result).toBe("px-2 py-3");
  });

  it("handles conditional classes", () => {
    const isHidden = false;
    const result = cn("base", isHidden && "hidden");
    expect(result).toBe("base");
  });

  it("deduplicates conflicting tailwind classes", () => {
    const result = cn("px-2", "px-4");
    expect(result).toBe("px-4");
  });

  it("handles undefined and null inputs", () => {
    const result = cn("base", undefined, null, "extra");
    expect(result).toBe("base extra");
  });

  it("handles empty call", () => {
    const result = cn();
    expect(result).toBe("");
  });
});
