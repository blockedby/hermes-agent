export type TelegramLaunchParams = {
  initData: string;
  startParam?: string;
};

const TELEGRAM_INIT_DATA_STORAGE_KEY = "hermes.telegram.initData";
const TELEGRAM_START_PARAM_STORAGE_KEY = "hermes.telegram.startParam";

export function parseTelegramLaunchParamsHash(hash: string): TelegramLaunchParams | null {
  const normalized = hash.startsWith("#") ? hash.slice(1) : hash;
  if (!normalized) {
    return null;
  }

  const params = new URLSearchParams(normalized);
  const initData = params.get("tgWebAppData") ?? "";
  if (!initData) {
    return null;
  }

  return {
    initData,
    startParam: params.get("tgWebAppStartParam") ?? undefined,
  };
}

export function parseTelegramUserFromInitData(initData: string): TelegramWebAppUser | undefined {
  try {
    const userJson = new URLSearchParams(initData).get("user");
    if (!userJson) {
      return undefined;
    }
    const parsed = JSON.parse(userJson) as Partial<TelegramWebAppUser>;
    if (typeof parsed.id !== "number" || !parsed.first_name) {
      return undefined;
    }
    return parsed as TelegramWebAppUser;
  } catch {
    return undefined;
  }
}

export function getStoredTelegramLaunchParams(storage: Storage | undefined): TelegramLaunchParams | null {
  if (!storage) {
    return null;
  }
  try {
    const initData = storage.getItem(TELEGRAM_INIT_DATA_STORAGE_KEY) ?? "";
    if (!initData) {
      return null;
    }
    return {
      initData,
      startParam: storage.getItem(TELEGRAM_START_PARAM_STORAGE_KEY) ?? undefined,
    };
  } catch {
    return null;
  }
}

export function storeTelegramLaunchParams(storage: Storage | undefined, params: TelegramLaunchParams): void {
  if (!storage || !params.initData) {
    return;
  }
  try {
    storage.setItem(TELEGRAM_INIT_DATA_STORAGE_KEY, params.initData);
    if (params.startParam) {
      storage.setItem(TELEGRAM_START_PARAM_STORAGE_KEY, params.startParam);
    }
  } catch {
    // Best-effort only: Telegram auth still works for the current page load.
  }
}
