import { afterEach, describe, expect, it, vi } from "vitest";

import {
  TelegramAdminAuthError,
  validateTelegramAdminInitData,
} from "./telegram-auth";
import {
  signedInitDataFor,
  tamperInitDataHash,
  TEST_ADMIN_USER_ID,
  TEST_BOT_TOKEN,
  TEST_NON_ADMIN_USER_ID,
} from "@/test/telegram-init-data-fixtures";

function setAuthEnv(adminUserIds = String(TEST_ADMIN_USER_ID)) {
  vi.stubEnv("TELEGRAM_BOT_TOKEN", TEST_BOT_TOKEN);
  vi.stubEnv("TELEGRAM_ADMIN_USER_IDS", adminUserIds);
}

describe("validateTelegramAdminInitData", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("accepts a valid Telegram Web App initData fixture for an admin user", () => {
    setAuthEnv();

    const session = validateTelegramAdminInitData(signedInitDataFor(TEST_ADMIN_USER_ID));

    expect(session).toEqual({
      telegramUserId: TEST_ADMIN_USER_ID,
      username: "ada_admin",
      firstName: "Ada",
    });
  });

  it("rejects valid Telegram initData when the user is not on the admin allowlist", () => {
    setAuthEnv();

    expect(() =>
      validateTelegramAdminInitData(signedInitDataFor(TEST_NON_ADMIN_USER_ID)),
    ).toThrowError(expect.objectContaining({ code: "forbidden" }));
  });

  it("rejects initData with an invalid signature", () => {
    setAuthEnv();

    expect(() =>
      validateTelegramAdminInitData(tamperInitDataHash(signedInitDataFor(TEST_ADMIN_USER_ID))),
    ).toThrowError(expect.objectContaining({ code: "unauthorized" }));
  });

  it("rejects expired auth_date values", () => {
    setAuthEnv();
    const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);

    expect(() =>
      validateTelegramAdminInitData(signedInitDataFor(TEST_ADMIN_USER_ID, tenMinutesAgo)),
    ).toThrow(TelegramAdminAuthError);
  });

  it("fails closed when TELEGRAM_BOT_TOKEN is missing", () => {
    vi.stubEnv("TELEGRAM_BOT_TOKEN", "");
    vi.stubEnv("TELEGRAM_ADMIN_USER_IDS", String(TEST_ADMIN_USER_ID));

    expect(() =>
      validateTelegramAdminInitData(signedInitDataFor(TEST_ADMIN_USER_ID)),
    ).toThrowError(expect.objectContaining({ code: "config_error" }));
  });
});
