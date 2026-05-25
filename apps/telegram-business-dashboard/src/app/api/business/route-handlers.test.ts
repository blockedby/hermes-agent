import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";

import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET as getChats } from "./chats/route";
import { GET as getChat } from "./chats/[token]/route";
import { POST as postMode } from "./chats/[token]/mode/route";
import { POST as postDraft } from "./chats/[token]/draft/route";
import { GET as getHistory } from "./chats/[token]/history/route";
import {
  signedInitDataFor,
  tamperInitDataHash,
  TEST_ADMIN_USER_ID,
  TEST_BOT_TOKEN,
  TEST_NON_ADMIN_USER_ID,
} from "@/test/telegram-init-data-fixtures";

const APP_ROOT = process.cwd();
const API_BASE_URL = "https://hermes.example.test/dashboard";
const API_TOKEN = "server-token-never-for-browser";
const CHAT_TOKEN = "chat-token-1";

function setEnv(adminUserIds = String(TEST_ADMIN_USER_ID)) {
  vi.stubEnv("TELEGRAM_BOT_TOKEN", TEST_BOT_TOKEN);
  vi.stubEnv("TELEGRAM_ADMIN_USER_IDS", adminUserIds);
  vi.stubEnv("HERMES_DASHBOARD_API_BASE_URL", API_BASE_URL);
  vi.stubEnv("HERMES_DASHBOARD_API_TOKEN", API_TOKEN);
}

function mockFetch(status: number, body: unknown = {}) {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(body), {
      status,
      headers: { "content-type": "application/json" },
    }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function authHeaders(initData = signedInitDataFor(TEST_ADMIN_USER_ID)) {
  return { "x-telegram-init-data": initData };
}

type NextRequestInit = ConstructorParameters<typeof NextRequest>[1];

function request(url: string, init?: NextRequestInit) {
  return new NextRequest(url, init);
}

function tokenCtx(token = CHAT_TOKEN) {
  return { params: Promise.resolve({ token }) };
}

async function jsonOf(response: Response) {
  return response.json() as Promise<unknown>;
}

function walkFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      return walkFiles(path);
    }
    return [path];
  });
}

describe("Telegram Business dashboard BFF route handlers", () => {
  beforeEach(() => {
    setEnv();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("validates Telegram admin initData before proxying GET /api/business/chats", async () => {
    const fetchMock = mockFetch(200, {
      chats: [{ token: CHAT_TOKEN, displayName: "Customer", mode: "watch" }],
      count: 1,
    });

    const response = await getChats(
      request("http://localhost/api/business/chats?mode=watch&q=ada", {
        headers: authHeaders(),
      }),
    );

    await expect(jsonOf(response)).resolves.toEqual({
      chats: [{ token: CHAT_TOKEN, displayName: "Customer", mode: "watch" }],
      count: 1,
    });
    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://hermes.example.test/dashboard/api/business/chats?mode=watch&q=ada",
      expect.objectContaining({
        method: "GET",
        cache: "no-store",
        headers: expect.objectContaining({
          authorization: `Bearer ${API_TOKEN}`,
          "x-telegram-user-id": String(TEST_ADMIN_USER_ID),
        }),
      }),
    );
  });

  it("rejects non-admin Telegram users without calling Hermes", async () => {
    const fetchMock = mockFetch(200, { chats: [] });

    const response = await getChats(
      request("http://localhost/api/business/chats", {
        headers: authHeaders(signedInitDataFor(TEST_NON_ADMIN_USER_ID)),
      }),
    );

    await expect(jsonOf(response)).resolves.toEqual({ ok: false, error: "forbidden" });
    expect(response.status).toBe(403);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("rejects invalid Telegram initData without calling Hermes", async () => {
    const fetchMock = mockFetch(200, { chats: [] });

    const response = await getChat(
      request("http://localhost/api/business/chats/chat-token-1", {
        headers: authHeaders(tamperInitDataHash(signedInitDataFor(TEST_ADMIN_USER_ID))),
      }),
      tokenCtx(),
    );

    await expect(jsonOf(response)).resolves.toEqual({ ok: false, error: "unauthorized" });
    expect(response.status).toBe(401);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("proxies chat detail and bounded history with actor headers", async () => {
    const fetchMock = mockFetch(200, { chat: { token: CHAT_TOKEN }, history: [] });

    const detailResponse = await getChat(
      request("http://localhost/api/business/chats/chat-token-1", { headers: authHeaders() }),
      tokenCtx(),
    );
    const historyResponse = await getHistory(
      request("http://localhost/api/business/chats/chat-token-1/history?limit=10&cursor=abc", {
        headers: authHeaders(),
      }),
      tokenCtx(),
    );

    expect(detailResponse.status).toBe(200);
    expect(historyResponse.status).toBe(200);
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "https://hermes.example.test/dashboard/api/business/chats/chat-token-1",
      expect.objectContaining({ method: "GET" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "https://hermes.example.test/dashboard/api/business/chats/chat-token-1/history?limit=10&cursor=abc",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ "x-telegram-user-id": String(TEST_ADMIN_USER_ID) }),
      }),
    );
  });

  it("POSTs mode changes with actor header and actor body without forwarding initData", async () => {
    const fetchMock = mockFetch(200, { chat: { token: CHAT_TOKEN, mode: "auto" } });

    const response = await postMode(
      request("http://localhost/api/business/chats/chat-token-1/mode", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ initData: signedInitDataFor(TEST_ADMIN_USER_ID), mode: "auto" }),
      }),
      tokenCtx(),
    );

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://hermes.example.test/dashboard/api/business/chats/chat-token-1/mode",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          authorization: `Bearer ${API_TOKEN}`,
          "content-type": "application/json",
          "x-telegram-user-id": String(TEST_ADMIN_USER_ID),
        }),
        body: JSON.stringify({ mode: "auto", actorUserId: String(TEST_ADMIN_USER_ID) }),
      }),
    );
    const upstreamBody = JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body));
    expect(upstreamBody).not.toHaveProperty("initData");
  });

  it("POSTs draft requests with source latest and actor body", async () => {
    const fetchMock = mockFetch(202, {
      draft: { status: "queued", chatToken: CHAT_TOKEN, source: "latest", sentToCustomer: false },
    });

    const response = await postDraft(
      request("http://localhost/api/business/chats/chat-token-1/draft", {
        method: "POST",
        headers: { "content-type": "application/json", ...authHeaders() },
        body: JSON.stringify({ source: "latest", prompt: "focus on warranty" }),
      }),
      tokenCtx(),
    );

    expect(response.status).toBe(202);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://hermes.example.test/dashboard/api/business/chats/chat-token-1/draft",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ source: "latest", prompt: "focus on warranty", actorUserId: String(TEST_ADMIN_USER_ID) }),
      }),
    );
  });

  it("requires Telegram initData on every Business route before calling Hermes", async () => {
    const fetchMock = mockFetch(200, { ok: true });
    const routes = [
      () => getChats(request("http://localhost/api/business/chats")),
      () => getChat(request("http://localhost/api/business/chats/chat-token-1"), tokenCtx()),
      () => getHistory(request("http://localhost/api/business/chats/chat-token-1/history"), tokenCtx()),
      () =>
        postMode(
          request("http://localhost/api/business/chats/chat-token-1/mode", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ mode: "watch" }),
          }),
          tokenCtx(),
        ),
      () =>
        postDraft(
          request("http://localhost/api/business/chats/chat-token-1/draft", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ source: "latest" }),
          }),
          tokenCtx(),
        ),
    ];

    for (const callRoute of routes) {
      const response = await callRoute();
      await expect(jsonOf(response)).resolves.toEqual({ ok: false, error: "missing_init_data" });
      expect(response.status).toBe(400);
    }
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("keeps the Hermes service token server-only and out of client-facing source", () => {
    const envExample = readFileSync(join(APP_ROOT, ".env.example"), "utf8");
    expect(envExample).toContain("HERMES_DASHBOARD_API_TOKEN=");
    expect(envExample).not.toContain("NEXT_PUBLIC_HERMES_DASHBOARD_API_TOKEN");

    const clientFacingFiles = walkFiles(join(APP_ROOT, "src")).filter((file) => {
      const normalized = relative(APP_ROOT, file).split("\\").join("/");
      return (
        /\.(ts|tsx)$/.test(normalized) &&
        !normalized.includes("/lib/server/") &&
        !normalized.includes("/app/api/") &&
        !normalized.includes("/test/")
      );
    });

    expect(clientFacingFiles.length).toBeGreaterThan(0);
    for (const file of clientFacingFiles) {
      expect(readFileSync(file, "utf8"), relative(APP_ROOT, file)).not.toContain(
        "HERMES_DASHBOARD_API_TOKEN",
      );
    }
  });

  it("maps Hermes auth failures to UI-safe BFF errors", async () => {
    mockFetch(403, { error: { code: "invalid_bearer_token", message: "Bearer token is invalid." } });

    const response = await getChats(
      request("http://localhost/api/business/chats", { headers: authHeaders() }),
    );

    await expect(jsonOf(response)).resolves.toEqual({ ok: false, error: "dashboard_auth_failed" });
    expect(response.status).toBe(502);
  });

  it("maps nested Python API validation errors to public client errors", async () => {
    const fetchMock = mockFetch(400, {
      error: { code: "invalid_mode", message: "Invalid Business chat mode." },
    });

    const invalidMode = await postMode(
      request("http://localhost/api/business/chats/chat-token-1/mode", {
        method: "POST",
        headers: { "content-type": "application/json", ...authHeaders() },
        body: JSON.stringify({ mode: "manual-send" }),
      }),
      tokenCtx(),
    );
    await expect(jsonOf(invalidMode)).resolves.toEqual({ ok: false, error: "invalid_mode" });
    expect(invalidMode.status).toBe(400);

    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ error: { code: "missing_latest_message", message: "No latest message." } }),
        { status: 409, headers: { "content-type": "application/json" } },
      ),
    );
    const missingLatestMessage = await postDraft(
      request("http://localhost/api/business/chats/chat-token-1/draft", {
        method: "POST",
        headers: { "content-type": "application/json", ...authHeaders() },
        body: JSON.stringify({ source: "latest" }),
      }),
      tokenCtx(),
    );
    await expect(jsonOf(missingLatestMessage)).resolves.toEqual({ ok: false, error: "missing_latest_message" });
    expect(missingLatestMessage.status).toBe(409);
  });

  it("maps Hermes not found and server failures to UI-safe responses", async () => {
    const fetchMock = mockFetch(404, { error: "chat_not_found", message: "Business chat not found." });

    const notFound = await getChat(
      request("http://localhost/api/business/chats/missing", { headers: authHeaders() }),
      tokenCtx("missing"),
    );
    await expect(jsonOf(notFound)).resolves.toEqual({ ok: false, error: "not_found" });
    expect(notFound.status).toBe(404);

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ error: "traceback", message: "internal detail" }), { status: 500 }),
    );
    const failed = await getChats(
      request("http://localhost/api/business/chats", { headers: authHeaders() }),
    );
    await expect(jsonOf(failed)).resolves.toEqual({ ok: false, error: "dashboard_unavailable" });
    expect(failed.status).toBe(502);
  });

  it("maps network failures and missing Hermes config to UI-safe responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("connection refused")));

    const networkFailure = await getChats(
      request("http://localhost/api/business/chats", { headers: authHeaders() }),
    );
    await expect(jsonOf(networkFailure)).resolves.toEqual({ ok: false, error: "dashboard_unavailable" });
    expect(networkFailure.status).toBe(502);

    vi.stubEnv("HERMES_DASHBOARD_API_BASE_URL", "");
    const configFailure = await getChats(
      request("http://localhost/api/business/chats", { headers: authHeaders() }),
    );
    await expect(jsonOf(configFailure)).resolves.toEqual({ ok: false, error: "dashboard_not_configured" });
    expect(configFailure.status).toBe(500);
  });
});
