"use client";

import { useEffect, useState } from "react";

export type TelegramWebAppState =
  | { status: "loading" }
  | { status: "missing" }
  | { status: "ready"; initData: string; user?: TelegramWebAppUser };

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
      if (webApp?.initData) {
        webApp.ready();
        webApp.expand();
        applyTelegramTheme(webApp);
        setState({
          status: "ready",
          initData: webApp.initData,
          user: webApp.initDataUnsafe.user,
        });
        return;
      }

      attempts += 1;
      if (attempts < 20) {
        timer = window.setTimeout(checkTelegram, 50);
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
