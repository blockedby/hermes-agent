"use client";

import { useEffect, useState } from "react";

export type TelegramWebAppState =
  | { status: "loading" }
  | { status: "missing" }
  | { status: "ready"; initData: string; user?: TelegramWebAppUser };

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
