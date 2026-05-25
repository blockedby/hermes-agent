import { afterEach, describe, expect, it, vi } from "vitest";

import {
  fetchBusinessChatDetail,
  fetchBusinessChats,
  generateBusinessDraft,
  updateBusinessChatMode,
} from "./api";

const INIT_DATA = "query_id=test&hash=signed";

function mockFetch(status: number, body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(body), {
      status,
      headers: { "content-type": "application/json" },
    }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("Business dashboard client API", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches chats and detail with Telegram initData only in request headers", async () => {
    const fetchMock = mockFetch(200, { chats: [], count: 0 });

    await expect(fetchBusinessChats(INIT_DATA)).resolves.toEqual({ chats: [], count: 0 });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/business/chats",
      expect.objectContaining({
        method: "GET",
        headers: { "x-telegram-init-data": INIT_DATA, accept: "application/json" },
      }),
    );

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ chat: { token: "tok-1", displayName: "Ada", mode: "watch" }, history: [] }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    await fetchBusinessChatDetail("tok-1", INIT_DATA);
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/business/chats/tok-1",
      expect.objectContaining({
        method: "GET",
        headers: { "x-telegram-init-data": INIT_DATA, accept: "application/json" },
      }),
    );
  });

  it("posts mode and draft actions through BFF routes without exposing service tokens", async () => {
    const fetchMock = mockFetch(200, { chat: { token: "tok-1", mode: "auto" } });

    await updateBusinessChatMode("tok-1", "auto", INIT_DATA);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/business/chats/tok-1/mode",
      expect.objectContaining({
        method: "POST",
        headers: {
          "x-telegram-init-data": INIT_DATA,
          accept: "application/json",
          "content-type": "application/json",
        },
        body: JSON.stringify({ mode: "auto" }),
      }),
    );
    expect(String(fetchMock.mock.calls[0]?.[1]?.body)).not.toContain("HERMES" + "_DASHBOARD" + "_API" + "_TOKEN");

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ draft: { status: "queued", chatToken: "tok-1", source: "latest", sentToCustomer: false } }), {
        status: 202,
        headers: { "content-type": "application/json" },
      }),
    );
    await generateBusinessDraft("tok-1", INIT_DATA, "  mention spring launch  ");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/business/chats/tok-1/draft",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ source: "latest", prompt: "mention spring launch" }),
      }),
    );

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ draft: { status: "queued", chatToken: "tok-1", source: "latest", sentToCustomer: false } }), {
        status: 202,
        headers: { "content-type": "application/json" },
      }),
    );
    await generateBusinessDraft("tok-1", INIT_DATA, "   ");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/business/chats/tok-1/draft",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ source: "latest" }),
      }),
    );
  });

  it("maps BFF failures to user-safe client errors", async () => {
    mockFetch(403, { ok: false, error: "forbidden" });

    await expect(fetchBusinessChats(INIT_DATA)).rejects.toMatchObject({
      status: 403,
      code: "forbidden",
      message: "forbidden",
    });
  });
});
