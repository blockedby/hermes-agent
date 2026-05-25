import "server-only";

import { parse, validate } from "@tma.js/init-data-node";

const INIT_DATA_MAX_AGE_SECONDS = 5 * 60;

export type TelegramAdminSession = {
  telegramUserId: number;
  username?: string;
  firstName?: string;
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

export function validateTelegramAdminInitData(initData: string): TelegramAdminSession {
  const botToken = process.env.TELEGRAM_BOT_TOKEN;
  if (!botToken) {
    throw new TelegramAdminAuthError("config_error", "TELEGRAM_BOT_TOKEN is not configured");
  }
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

  if (!parseAdminUserIds().has(telegramUserId)) {
    throw new TelegramAdminAuthError("forbidden", "admin access required");
  }

  return {
    telegramUserId,
    username: user?.username,
    firstName: user?.first_name,
  };
}
