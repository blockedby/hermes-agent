import type {
  BusinessChatMode,
  BusinessChatResponse,
  BusinessChatsResponse,
  BusinessDraftResponse,
  BusinessHistoryResponse,
  BusinessModeResponse,
} from "./types";

export class BusinessApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message = code) {
    super(message);
    this.name = "BusinessApiError";
    this.status = status;
    this.code = code;
  }
}

type RequestOptions = {
  method?: "GET" | "POST";
  initData: string;
  body?: Record<string, unknown>;
};

async function readJson(response: Response): Promise<Record<string, unknown> | null> {
  try {
    const value = (await response.json()) as unknown;
    return value && typeof value === "object" ? (value as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

async function businessFetch<T>(path: string, { method = "GET", initData, body }: RequestOptions): Promise<T> {
  const headers: Record<string, string> = {
    "x-telegram-init-data": initData,
    accept: "application/json",
  };
  const requestInit: RequestInit = { method, headers, cache: "no-store" };

  if (body) {
    headers["content-type"] = "application/json";
    requestInit.body = JSON.stringify(body);
  }

  const response = await fetch(path, requestInit);
  const payload = await readJson(response);
  if (!response.ok) {
    const code = typeof payload?.error === "string" ? payload.error : "dashboard_unavailable";
    throw new BusinessApiError(response.status, code, code);
  }

  return payload as T;
}

export function fetchBusinessChats(initData: string): Promise<BusinessChatsResponse> {
  return businessFetch<BusinessChatsResponse>("/api/business/chats", { initData });
}

export function fetchBusinessChatDetail(token: string, initData: string): Promise<BusinessChatResponse> {
  return businessFetch<BusinessChatResponse>(`/api/business/chats/${encodeURIComponent(token)}`, { initData });
}

export function fetchBusinessHistory(token: string, initData: string): Promise<BusinessHistoryResponse> {
  return businessFetch<BusinessHistoryResponse>(`/api/business/chats/${encodeURIComponent(token)}/history`, {
    initData,
  });
}

export function updateBusinessChatMode(
  token: string,
  mode: BusinessChatMode,
  initData: string,
): Promise<BusinessModeResponse> {
  return businessFetch<BusinessModeResponse>(`/api/business/chats/${encodeURIComponent(token)}/mode`, {
    method: "POST",
    initData,
    body: { mode },
  });
}

export function generateBusinessDraft(
  token: string,
  initData: string,
  prompt?: string,
): Promise<BusinessDraftResponse> {
  const normalizedPrompt = prompt?.trim() ?? "";
  return businessFetch<BusinessDraftResponse>(`/api/business/chats/${encodeURIComponent(token)}/draft`, {
    method: "POST",
    initData,
    body: normalizedPrompt ? { source: "latest", prompt: normalizedPrompt } : { source: "latest" },
  });
}
