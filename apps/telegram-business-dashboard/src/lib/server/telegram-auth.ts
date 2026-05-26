import "server-only";

import { createHmac, timingSafeEqual } from "node:crypto";

import { parse, validate } from "@tma.js/init-data-node";

const INIT_DATA_MAX_AGE_SECONDS = 5 * 60;

export const DASHBOARD_SESSION_COOKIE_NAME = "hermes_tg_dashboard_session";
export const DASHBOARD_SESSION_MAX_AGE_SECONDS = 24 * 60 * 60;

export type TelegramAdminSession = {
  telegramUserId: number;
  username?: string;
  firstName?: string;
};

type DashboardSessionPayload = {
  v: 1;
  telegramUserId: number;
  username?: string;
  firstName?: string;
  iat: number;
  exp: number;
};

export class TelegramAdminAuthError extends Error {
  constructor(
    public readonly code: "config_error" | "unauthorized" | "forbidden",
    message: string,
  ) {
    super(message);
    this.name = "TelegramAdminAuthError";
  }
}

function parseAdminUserIds(): Set<number> {
  return new Set(
    (process.env.TELEGRAM_ADMIN_USER_IDS ?? "")
      .split(",")
      .map((value) => Number(value.trim()))
      .filter((value) => Number.isSafeInteger(value) && value > 0),
  );
}

function requireBotToken(): string {
  const botToken = process.env.TELEGRAM_BOT_TOKEN;
  if (!botToken) {
    throw new TelegramAdminAuthError("config_error", "TELEGRAM_BOT_TOKEN is not configured");
  }
  return botToken;
}

function assertAdminUserId(telegramUserId: number) {
  if (!parseAdminUserIds().has(telegramUserId)) {
    throw new TelegramAdminAuthError("forbidden", "admin access required");
  }
}

function signDashboardSession(payload: string, secret: string): string {
  return createHmac("sha256", secret).update(payload).digest("base64url");
}

function parseDashboardSessionPayload(payload: unknown): DashboardSessionPayload {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new TelegramAdminAuthError("unauthorized", "invalid dashboard session");
  }

  const value = payload as Partial<DashboardSessionPayload>;
  const telegramUserId = value.telegramUserId;
  const issuedAt = value.iat;
  const expiresAt = value.exp;
  if (
    value.v !== 1 ||
    typeof telegramUserId !== "number" ||
    !Number.isSafeInteger(telegramUserId) ||
    telegramUserId <= 0 ||
    typeof issuedAt !== "number" ||
    !Number.isSafeInteger(issuedAt) ||
    typeof expiresAt !== "number" ||
    !Number.isSafeInteger(expiresAt)
  ) {
    throw new TelegramAdminAuthError("unauthorized", "invalid dashboard session");
  }

  return {
    v: 1,
    telegramUserId,
    username: typeof value.username === "string" ? value.username : undefined,
    firstName: typeof value.firstName === "string" ? value.firstName : undefined,
    iat: issuedAt,
    exp: expiresAt,
  };
}

export function dashboardSessionCookieOptions() {
  return {
    httpOnly: true,
    secure: true,
    sameSite: "none" as const,
    path: "/",
    maxAge: DASHBOARD_SESSION_MAX_AGE_SECONDS,
    expires: new Date(Date.now() + DASHBOARD_SESSION_MAX_AGE_SECONDS * 1000),
  };
}

export function issueDashboardSessionCookie(session: TelegramAdminSession): string {
  const secret = requireBotToken();
  const now = Math.floor(Date.now() / 1000);
  const payload: DashboardSessionPayload = {
    v: 1,
    telegramUserId: session.telegramUserId,
    username: session.username,
    firstName: session.firstName,
    iat: now,
    exp: now + DASHBOARD_SESSION_MAX_AGE_SECONDS,
  };
  const payloadBase64 = Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
  return `${payloadBase64}.${signDashboardSession(payloadBase64, secret)}`;
}

export function validateDashboardSessionCookie(cookieValue: string): TelegramAdminSession {
  const secret = requireBotToken();
  if (!cookieValue) {
    throw new TelegramAdminAuthError("unauthorized", "missing dashboard session");
  }

  const [payloadBase64, signature, extra] = cookieValue.split(".");
  if (!payloadBase64 || !signature || extra !== undefined) {
    throw new TelegramAdminAuthError("unauthorized", "invalid dashboard session");
  }

  const expectedSignature = signDashboardSession(payloadBase64, secret);
  const providedSignature = Buffer.from(signature, "base64url");
  const expectedSignatureBuffer = Buffer.from(expectedSignature, "base64url");
  if (
    providedSignature.length !== expectedSignatureBuffer.length ||
    !timingSafeEqual(providedSignature, expectedSignatureBuffer)
  ) {
    throw new TelegramAdminAuthError("unauthorized", "invalid dashboard session");
  }

  let payload: DashboardSessionPayload;
  try {
    payload = parseDashboardSessionPayload(
      JSON.parse(Buffer.from(payloadBase64, "base64url").toString("utf8")) as unknown,
    );
  } catch (error) {
    if (error instanceof TelegramAdminAuthError) {
      throw error;
    }
    throw new TelegramAdminAuthError("unauthorized", "invalid dashboard session");
  }

  if (payload.exp <= Math.floor(Date.now() / 1000)) {
    throw new TelegramAdminAuthError("unauthorized", "dashboard session expired");
  }

  assertAdminUserId(payload.telegramUserId);
  return {
    telegramUserId: payload.telegramUserId,
    username: payload.username,
    firstName: payload.firstName,
  };
}

export function validateTelegramAdminInitData(initData: string): TelegramAdminSession {
  const botToken = requireBotToken();
  if (!initData) {
    throw new TelegramAdminAuthError("unauthorized", "missing initData");
  }

  try {
    validate(initData, botToken, { expiresIn: INIT_DATA_MAX_AGE_SECONDS });
  } catch (error) {
    throw new TelegramAdminAuthError(
      "unauthorized",
      error instanceof Error ? error.message : "invalid Telegram initData",
    );
  }

  const parsed = parse(initData);
  const user = parsed.user;
  const telegramUserId = Number(user?.id);
  if (!Number.isSafeInteger(telegramUserId) || telegramUserId <= 0) {
    throw new TelegramAdminAuthError("unauthorized", "missing Telegram user");
  }

  assertAdminUserId(telegramUserId);

  return {
    telegramUserId,
    username: user?.username,
    firstName: user?.first_name,
  };
}
