import "server-only";

import { NextRequest, NextResponse } from "next/server";

import {
  HermesDashboardConfigError,
  type HermesDashboardResponse,
} from "./hermes-dashboard-api";
import {
  TelegramAdminAuthError,
  validateTelegramAdminInitData,
  type TelegramAdminSession,
} from "./telegram-auth";

export type RequestBody = Record<string, unknown>;

export function authenticateTelegramAdmin(
  request: NextRequest,
  body?: RequestBody | null,
): TelegramAdminSession | NextResponse {
  const initDataFromHeader = request.headers.get("x-telegram-init-data");
  const initDataFromBody = typeof body?.initData === "string" ? body.initData : "";
  const initData = initDataFromHeader || initDataFromBody;

  if (!initData) {
    return NextResponse.json({ ok: false, error: "missing_init_data" }, { status: 400 });
  }

  try {
    return validateTelegramAdminInitData(initData);
  } catch (error) {
    if (error instanceof TelegramAdminAuthError) {
      if (error.code === "forbidden") {
        return NextResponse.json({ ok: false, error: "forbidden" }, { status: 403 });
      }
      if (error.code === "config_error") {
        return NextResponse.json({ ok: false, error: "auth_not_configured" }, { status: 500 });
      }
    }
    return NextResponse.json({ ok: false, error: "unauthorized" }, { status: 401 });
  }
}

export async function parseJsonBody(request: NextRequest): Promise<RequestBody | NextResponse> {
  try {
    const value = (await request.json()) as unknown;
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      return NextResponse.json({ ok: false, error: "invalid_json" }, { status: 400 });
    }
    return value as RequestBody;
  } catch {
    return NextResponse.json({ ok: false, error: "invalid_json" }, { status: 400 });
  }
}

export function isNextResponse(value: unknown): value is NextResponse {
  return value instanceof NextResponse;
}

function upstreamErrorCode(body: Record<string, unknown> | null): string {
  return typeof body?.error === "string" ? body.error : "dashboard_error";
}

function publicClientError(code: string): string {
  const allowed = new Set([
    "invalid_mode",
    "invalid_source",
    "missing_latest_message",
    "chat_not_found",
  ]);
  return allowed.has(code) ? code : "dashboard_error";
}

export function toSafeHermesResponse<T>({ status, body }: HermesDashboardResponse<T>): NextResponse {
  const responseBody = body && typeof body === "object" ? (body as Record<string, unknown>) : null;

  if (status >= 200 && status < 300) {
    return NextResponse.json(responseBody ?? {}, { status });
  }

  if (status === 401 || status === 403) {
    return NextResponse.json({ ok: false, error: "dashboard_auth_failed" }, { status: 502 });
  }

  if (status === 404) {
    return NextResponse.json({ ok: false, error: "not_found" }, { status: 404 });
  }

  if (status >= 500) {
    return NextResponse.json({ ok: false, error: "dashboard_unavailable" }, { status: 502 });
  }

  return NextResponse.json(
    { ok: false, error: publicClientError(upstreamErrorCode(responseBody)) },
    { status },
  );
}

export async function safeHermesResponse<T>(
  call: () => Promise<HermesDashboardResponse<T>>,
): Promise<NextResponse> {
  try {
    return toSafeHermesResponse(await call());
  } catch (error) {
    if (error instanceof HermesDashboardConfigError) {
      return NextResponse.json({ ok: false, error: "dashboard_not_configured" }, { status: 500 });
    }
    return NextResponse.json({ ok: false, error: "dashboard_unavailable" }, { status: 502 });
  }
}

export function postBodyWithoutInitData(body: RequestBody, allowedKeys: string[]): RequestBody {
  return Object.fromEntries(
    allowedKeys
      .filter((key) => key in body)
      .map((key) => [key, body[key]]),
  );
}
