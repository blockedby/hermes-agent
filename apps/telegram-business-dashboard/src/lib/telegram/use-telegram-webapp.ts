"use client";

import { useEffect, useState } from "react";

import {
  getStoredTelegramLaunchParams,
  parseTelegramLaunchParamsHash,
  parseTelegramUserFromInitData,
  storeTelegramLaunchParams,
  type TelegramLaunchParams,
} from "./launch-params";

export type TelegramWebAppState =
  | { status: "loading" }
  | { status: "missing" }
  | { status: "ready"; initData: string; user?: TelegramWebAppUser; startParam?: string };

const TELEGRAM_THEME_VARIABLES: Record<string, string> = {
  bg_color: "--background",
  text_color: "--foreground",
  secondary_bg_color: "--card",
  hint_color: "--muted-foreground",
  button_color: "--primary",
  button_text_color: "--primary-foreground",
};

function applyTelegramTheme(webApp: TelegramWebApp) {
  const root = document.documentElement;
  root.classList.toggle("dark", webApp.colorScheme === "dark");

  for (const [telegramKey, cssVariable] of Object.entries(TELEGRAM_THEME_VARIABLES)) {
    const value = webApp.themeParams?.[telegramKey];
    if (value && /^#[0-9a-f]{6}$/i.test(value)) {
      root.style.setProperty(cssVariable, value);
    }
  }
}

function sessionStorageOrUndefined(): Storage | undefined {
  try {
    return window.sessionStorage;
  } catch {
    return undefined;
  }
}

function readTelegramLaunchParams(webApp?: TelegramWebApp): TelegramLaunchParams | null {
  if (webApp?.initData) {
    return {
      initData: webApp.initData,
      startParam: webApp.initDataUnsafe.start_param,
    };
  }

  const hashParams = parseTelegramLaunchParamsHash(window.location.hash);
  if (hashParams?.initData) {
    return hashParams;
  }

  return getStoredTelegramLaunchParams(sessionStorageOrUndefined());
}

export function useTelegramWebApp(): TelegramWebAppState {
  const [state, setState] = useState<TelegramWebAppState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    let attempts = 0;
    let timer: number | undefined;

    const checkTelegram = () => {
      if (cancelled) {
        return;
      }

      const webApp = window.Telegram?.WebApp;
      if (webApp) {
        webApp.ready();
        webApp.expand();
        applyTelegramTheme(webApp);
      }

      const launchParams = readTelegramLaunchParams(webApp);
      if (launchParams?.initData) {
        storeTelegramLaunchParams(sessionStorageOrUndefined(), launchParams);
        setState({
          status: "ready",
          initData: launchParams.initData,
          user: webApp?.initDataUnsafe.user ?? parseTelegramUserFromInitData(launchParams.initData),
          startParam: webApp?.initDataUnsafe.start_param ?? launchParams.startParam,
        });
        return;
      }

      attempts += 1;
      if (attempts < 100) {
        timer = window.setTimeout(checkTelegram, 100);
        return;
      }

      setState({ status: "missing" });
    };

    timer = window.setTimeout(checkTelegram, 0);

    return () => {
      cancelled = true;
      if (timer !== undefined) {
        window.clearTimeout(timer);
      }
    };
  }, []);

  return state;
}
