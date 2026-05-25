"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ChatDetailView } from "./chat-detail-view";
import {
  BusinessApiError,
  fetchBusinessChatDetail,
  fetchBusinessHistory,
  generateBusinessDraft,
  updateBusinessChatMode,
} from "@/lib/business/api";
import type { BusinessChatDetail, BusinessChatMode, BusinessHistoryEvent } from "@/lib/business/types";
import { useTelegramWebApp } from "@/lib/telegram/use-telegram-webapp";

type DetailStatus = "loading" | "ready" | "error" | "unauthorized" | "not-found";
type ActionStatus = { kind: "success" | "error" | "loading"; message: string } | null;

function statusForError(error: unknown): DetailStatus {
  if (error instanceof BusinessApiError) {
    if ([400, 401, 403].includes(error.status)) {
      return "unauthorized";
    }
    if (error.status === 404) {
      return "not-found";
    }
  }
  return "error";
}

function messageForError(error: unknown): string {
  if (error instanceof BusinessApiError) {
    return error.code;
  }
  return error instanceof Error ? error.message : "dashboard_unavailable";
}

export function ChatDetailShell({ token }: { token: string }) {
  const router = useRouter();
  const telegram = useTelegramWebApp();
  const [status, setStatus] = useState<DetailStatus>("loading");
  const [chat, setChat] = useState<BusinessChatDetail>();
  const [history, setHistory] = useState<BusinessHistoryEvent[]>([]);
  const [errorMessage, setErrorMessage] = useState<string>();
  const [actionStatus, setActionStatus] = useState<ActionStatus>(null);

  const loadDetail = useCallback(async () => {
    if (telegram.status === "missing") {
      setStatus("unauthorized");
      setChat(undefined);
      setHistory([]);
      return;
    }
    if (telegram.status !== "ready") {
      setStatus("loading");
      return;
    }

    setStatus("loading");
    setErrorMessage(undefined);
    try {
      const [detailResponse, historyResponse] = await Promise.all([
        fetchBusinessChatDetail(token, telegram.initData),
        fetchBusinessHistory(token, telegram.initData),
      ]);
      setChat(detailResponse.chat);
      setHistory(historyResponse.history ?? detailResponse.history ?? []);
      setStatus("ready");
    } catch (error) {
      setChat(undefined);
      setHistory([]);
      setErrorMessage(messageForError(error));
      setStatus(statusForError(error));
    }
  }, [telegram, token]);

  useEffect(() => {
    void Promise.resolve().then(loadDetail);
  }, [loadDetail]);

  const handleModeChange = useCallback(
    async (mode: BusinessChatMode) => {
      if (telegram.status !== "ready") {
        setActionStatus({ kind: "error", message: "Open from Telegram to change mode." });
        return;
      }
      setActionStatus({ kind: "loading", message: `Changing mode to ${mode}...` });
      try {
        const response = await updateBusinessChatMode(token, mode, telegram.initData);
        setChat(response.chat);
        setActionStatus({ kind: "success", message: `Mode changed to ${mode}.` });
        const historyResponse = await fetchBusinessHistory(token, telegram.initData);
        setHistory(historyResponse.history ?? []);
      } catch (error) {
        setActionStatus({ kind: "error", message: messageForError(error) });
      }
    },
    [telegram, token],
  );

  const handleGenerateDraft = useCallback(async () => {
    if (telegram.status !== "ready") {
      setActionStatus({ kind: "error", message: "Open from Telegram to generate a draft." });
      return;
    }
    setActionStatus({ kind: "loading", message: "Queueing draft generation..." });
    try {
      const response = await generateBusinessDraft(token, telegram.initData);
      setActionStatus({ kind: "success", message: `Draft ${response.draft.status}. Approval remains required.` });
      await loadDetail();
    } catch (error) {
      setActionStatus({ kind: "error", message: messageForError(error) });
    }
  }, [loadDetail, telegram, token]);

  return (
    <ChatDetailView
      chat={chat}
      history={history}
      status={status}
      errorMessage={errorMessage}
      actionStatus={actionStatus}
      onBack={() => router.push("/")}
      onRefresh={loadDetail}
      onModeChange={handleModeChange}
      onGenerateDraft={handleGenerateDraft}
    />
  );
}
