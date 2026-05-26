import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";

import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { POST } from "./route";
import { DASHBOARD_SESSION_COOKIE_NAME } from "@/lib/server/telegram-auth";
import {
  signedInitDataFor,
  tamperInitDataHash,
  TEST_ADMIN_USER_ID,
  TEST_BOT_TOKEN,
  TEST_NON_ADMIN_USER_ID,
} from "@/test/telegram-init-data-fixtures";

const APP_ROOT = process.cwd();

function setAuthEnv(adminUserIds = String(TEST_ADMIN_USER_ID)) {
  vi.stubEnv("TELEGRAM_BOT_TOKEN", TEST_BOT_TOKEN);
  vi.stubEnv("TELEGRAM_ADMIN_USER_IDS", adminUserIds);
}

async function postSession(initData: string) {
  return POST(
    new NextRequest("http://localhost/api/session", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ initData }),
    }),
  );
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

describe("POST /api/session", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns an admin session for valid Telegram Web App initData", async () => {
    setAuthEnv();

    const response = await postSession(signedInitDataFor(TEST_ADMIN_USER_ID));

    await expect(response.json()).resolves.toEqual({
      ok: true,
      user: {
        telegramUserId: TEST_ADMIN_USER_ID,
        username: "ada_admin",
        firstName: "Ada",
      },
    });
    expect(response.status).toBe(200);
    const setCookie = response.headers.get("set-cookie");
    expect(setCookie).toContain(`${DASHBOARD_SESSION_COOKIE_NAME}=`);
    expect(setCookie).toContain("HttpOnly");
    expect(setCookie).toContain("Secure");
    expect(setCookie).toContain("Path=/");
    expect(setCookie).toMatch(/SameSite=none/i);
    expect(setCookie).toContain("Max-Age=86400");
    expect(setCookie).toMatch(/Expires=/);
  });

  it("returns 403 for valid Telegram initData from a non-admin user", async () => {
    setAuthEnv();

    const response = await postSession(signedInitDataFor(TEST_NON_ADMIN_USER_ID));

    await expect(response.json()).resolves.toEqual({ ok: false, error: "forbidden" });
    expect(response.status).toBe(403);
  });

  it("returns 401 when initData has an invalid signature", async () => {
    setAuthEnv();

    const response = await postSession(
      tamperInitDataHash(signedInitDataFor(TEST_ADMIN_USER_ID)),
    );

    await expect(response.json()).resolves.toEqual({ ok: false, error: "unauthorized" });
    expect(response.status).toBe(401);
  });

  it("returns 401 when initData auth_date is expired", async () => {
    setAuthEnv();
    const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);

    const response = await postSession(signedInitDataFor(TEST_ADMIN_USER_ID, tenMinutesAgo));

    await expect(response.json()).resolves.toEqual({ ok: false, error: "unauthorized" });
    expect(response.status).toBe(401);
  });

  it("fails closed when TELEGRAM_BOT_TOKEN is missing", async () => {
    vi.stubEnv("TELEGRAM_BOT_TOKEN", "");
    vi.stubEnv("TELEGRAM_ADMIN_USER_IDS", String(TEST_ADMIN_USER_ID));

    const response = await postSession(signedInitDataFor(TEST_ADMIN_USER_ID));

    await expect(response.json()).resolves.toEqual({ ok: false, error: "auth_not_configured" });
    expect(response.status).toBe(500);
  });
});

describe("Telegram auth client exposure", () => {
  it("keeps TELEGRAM_BOT_TOKEN server-only and out of client-facing source", () => {
    const envExample = readFileSync(join(APP_ROOT, ".env.example"), "utf8");
    expect(envExample).toContain("TELEGRAM_BOT_TOKEN=");
    expect(envExample).not.toContain("NEXT_PUBLIC_TELEGRAM_BOT_TOKEN");

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
        "TELEGRAM_BOT_TOKEN",
      );
    }
  });
});
