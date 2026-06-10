import "server-only";

export type {
  BusinessChatDetail,
  BusinessChatMode,
  BusinessChatResponse,
  BusinessChatSummary,
  BusinessChatsResponse,
  BusinessDraftResponse,
  BusinessHistoryEvent,
  BusinessHistoryResponse,
  BusinessModeResponse,
  BusinessSettingsResponse,
} from "@/lib/business/types";

export type HermesDashboardResponse<T> = {
  status: number;
  body: T | Record<string, unknown> | null;
};

export class HermesDashboardConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "HermesDashboardConfigError";
  }
}

export type HermesDashboardRequestOptions = {
  method?: "GET" | "POST" | "PATCH";
  actorUserId: number;
  searchParams?: URLSearchParams;
  body?: Record<string, unknown>;
};

function dashboardUrl(path: string, searchParams?: URLSearchParams): string {
  const baseUrl = process.env.HERMES_DASHBOARD_API_BASE_URL?.trim();
  if (!baseUrl) {
    throw new HermesDashboardConfigError("HERMES_DASHBOARD_API_BASE_URL is not configured");
  }

  const normalizedBase = baseUrl.replace(/\/+$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${normalizedBase}${normalizedPath}`);
  searchParams?.forEach((value, key) => {
    if (value) {
      url.searchParams.set(key, value);
    }
  });
  return url.toString();
}

function dashboardToken(): string {
  const token = process.env.HERMES_DASHBOARD_API_TOKEN?.trim();
  if (!token) {
    throw new HermesDashboardConfigError("HERMES_DASHBOARD_API_TOKEN is not configured");
  }
  return token;
}

async function readJsonSafely(response: Response): Promise<Record<string, unknown> | null> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.toLowerCase().includes("json")) {
    return null;
  }

  try {
    const value = (await response.json()) as unknown;
    return value && typeof value === "object" ? (value as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

export async function callHermesDashboard<T>(
  path: string,
  { method = "GET", actorUserId, searchParams, body }: HermesDashboardRequestOptions,
): Promise<HermesDashboardResponse<T>> {
  const headers: Record<string, string> = {
    authorization: `Bearer ${dashboardToken()}`,
    accept: "application/json",
    "x-telegram-user-id": String(actorUserId),
  };

  const init: RequestInit = {
    method,
    headers,
    cache: "no-store",
  };

  if (body) {
    headers["content-type"] = "application/json";
    init.body = JSON.stringify(body);
  }

  const response = await fetch(dashboardUrl(path, searchParams), init);
  return {
    status: response.status,
    body: await readJsonSafely(response),
  };
}
