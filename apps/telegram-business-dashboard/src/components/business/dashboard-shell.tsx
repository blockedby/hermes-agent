"use client";

import { useCallback, useEffect, useState } from "react";

import { DashboardView } from "./dashboard-view";
import { BusinessApiError, fetchBusinessChats } from "@/lib/business/api";
import type { BusinessChatSummary } from "@/lib/business/types";
import type { ChatFilter } from "@/lib/business/view-model";
import { useTelegramWebApp } from "@/lib/telegram/use-telegram-webapp";

type DashboardStatus = "loading" | "ready" | "error" | "unauthorized";

function isUnauthorized(error: unknown): boolean {
  return error instanceof BusinessApiError && [400, 401, 403].includes(error.status);
}

function messageForError(error: unknown): string {
  if (error instanceof BusinessApiError) {
    return error.code;
  }
  return error instanceof Error ? error.message : "dashboard_unavailable";
}

export function BusinessDashboardShell() {
  const telegram = useTelegramWebApp();
  const [status, setStatus] = useState<DashboardStatus>("loading");
  const [chats, setChats] = useState<BusinessChatSummary[]>([]);
  const [filter, setFilter] = useState<ChatFilter>("all");
  const [query, setQuery] = useState("");
  const [errorMessage, setErrorMessage] = useState<string>();

  const loadChats = useCallback(async () => {
    if (telegram.status === "missing") {
      setStatus("unauthorized");
      setChats([]);
      return;
    }
    if (telegram.status !== "ready") {
      setStatus("loading");
      return;
    }

    setStatus("loading");
    setErrorMessage(undefined);
    try {
      const response = await fetchBusinessChats(telegram.initData);
      setChats(response.chats ?? []);
      setStatus("ready");
    } catch (error) {
      setChats([]);
      setErrorMessage(messageForError(error));
      setStatus(isUnauthorized(error) ? "unauthorized" : "error");
    }
  }, [telegram]);

  useEffect(() => {
    void Promise.resolve().then(loadChats);
  }, [loadChats]);

  return (
    <DashboardView
      chats={chats}
      filter={filter}
      query={query}
      status={status}
      errorMessage={errorMessage}
      onFilterChange={setFilter}
      onQueryChange={setQuery}
      onRefresh={loadChats}
    />
  );
}
