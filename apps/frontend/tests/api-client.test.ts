import { afterEach, describe, expect, it, vi } from "vitest";

import { apiRequest, openFile, uploadFile } from "../src/api/client";

describe("api client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("adds JSON headers and returns parsed payloads", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      apiRequest<{ ok: boolean }>("/api/demo", {
        method: "POST",
        headers: { Authorization: "Bearer token" },
      }),
    ).resolves.toEqual({ ok: true });

    const [, init] = fetchMock.mock.calls[0] ?? [];
    const headers = init?.headers as Headers;

    expect(init?.method).toBe("POST");
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.get("Authorization")).toBe("Bearer token");
  });

  it("surfaces backend detail messages on request failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "缺少考试数据" }), {
          status: 400,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(apiRequest("/api/demo")).rejects.toThrow("缺少考试数据");
  });

  it("uploads files with extra form fields", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ message: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const file = new File(["demo"], "demo.txt", { type: "text/plain" });

    await expect(uploadFile<{ message: string }>("/api/upload", file, { category: "archives" })).resolves.toEqual({
      message: "ok",
    });

    const [, init] = fetchMock.mock.calls[0] ?? [];
    const formData = init?.body as FormData;

    expect(init?.method).toBe("POST");
    expect(formData.get("file")).toBe(file);
    expect(formData.get("category")).toBe("archives");
  });

  it("opens files in a safe new tab", () => {
    const openSpy = vi.fn();
    vi.stubGlobal("window", { open: openSpy });

    openFile("/api/reports/download");

    expect(openSpy).toHaveBeenCalledWith("/api/reports/download", "_blank", "noopener,noreferrer");
  });
});
