import { describe, expect, it } from "vitest";

import {
  getStoredTelegramLaunchParams,
  parseTelegramLaunchParamsHash,
  parseTelegramUserFromInitData,
  storeTelegramLaunchParams,
} from "./launch-params";

class MemoryStorage implements Storage {
  private values = new Map<string, string>();
  get length() {
    return this.values.size;
  }
  clear() {
    this.values.clear();
  }
  getItem(key: string) {
    return this.values.get(key) ?? null;
  }
  key(index: number) {
    return Array.from(this.values.keys())[index] ?? null;
  }
  removeItem(key: string) {
    this.values.delete(key);
  }
  setItem(key: string, value: string) {
    this.values.set(key, value);
  }
}

const userJson = JSON.stringify({ id: 227049836, first_name: "Kirill", username: "blockedby" });
const rawInitData = new URLSearchParams({
  user: userJson,
  auth_date: "1779740000",
  hash: "signed-hash-placeholder",
}).toString();

describe("Telegram launch params", () => {
  it("extracts raw initData from Telegram URL hash", () => {
    const hash = new URLSearchParams({
      tgWebAppData: rawInitData,
      tgWebAppVersion: "8.0",
      tgWebAppStartParam: "dashboard",
    }).toString();

    expect(parseTelegramLaunchParamsHash(`#${hash}`)).toEqual({
      initData: rawInitData,
      startParam: "dashboard",
    });
  });

  it("returns null when the hash is not a Telegram Mini App launch", () => {
    expect(parseTelegramLaunchParamsHash("#foo=bar")).toBeNull();
    expect(parseTelegramLaunchParamsHash("")).toBeNull();
  });

  it("parses the user from raw initData as a fallback when WebApp.initDataUnsafe is unavailable", () => {
    expect(parseTelegramUserFromInitData(rawInitData)).toEqual({
      id: 227049836,
      first_name: "Kirill",
      username: "blockedby",
    });
  });

  it("stores launch params in session storage for Telegram webview refreshes", () => {
    const storage = new MemoryStorage();

    storeTelegramLaunchParams(storage, { initData: rawInitData, startParam: "dashboard" });

    expect(getStoredTelegramLaunchParams(storage)).toEqual({
      initData: rawInitData,
      startParam: "dashboard",
    });
  });
});
