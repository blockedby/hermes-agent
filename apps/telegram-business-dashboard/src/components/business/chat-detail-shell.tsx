"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ChatDetailView } from "./chat-detail-view";
import {
  BusinessApiError,
  fetchBusinessChatDetail,
  fetchBusinessChatSettings,
  fetchBusinessHistory,
  generateBusinessDraft,
  updateBusinessChatMode,
  updateBusinessChatSettings,
} from "@/lib/business/api";
import type {
  BusinessChatDetail,
  BusinessChatMode,
  BusinessDialogSettings,
  BusinessHistoryEvent,
  BusinessSettingsPatch,
} from "@/lib/business/types";
import { useTelegramWebApp } from "@/lib/telegram/use-telegram-webapp";

type DetailStatus = "loading" | "ready" | "error" | "unauthorized" | "not-found";
type SettingsStatus = "idle" | "loading" | "ready" | "error";
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

export type ChatDetailSnapshot = {
  chat: BusinessChatDetail;
  history: BusinessHistoryEvent[];
  settings?: BusinessDialogSettings;
  settingsErrorMessage?: string;
};

export async function fetchChatDetailSnapshot(token: string, initData: string): Promise<ChatDetailSnapshot> {
  const settingsRequest = fetchBusinessChatSettings(token, initData)
    .then((response) => ({ settings: response.settings }))
    .catch((error: unknown) => ({ settingsErrorMessage: messageForError(error) }));

  const [detailResponse, historyResponse, settingsResult] = await Promise.all([
    fetchBusinessChatDetail(token, initData),
    fetchBusinessHistory(token, initData),
    settingsRequest,
  ]);

  return {
    chat: detailResponse.chat,
    history: historyResponse.history ?? detailResponse.history ?? [],
    ...settingsResult,
  };
}

export async function saveBusinessChatSettingsSnapshot(
  token: string,
  initData: string,
  settingsDraft: BusinessDialogSettings,
): Promise<BusinessDialogSettings> {
  const response = await updateBusinessChatSettings(token, initData, settingsDraft);
  return response.settings;
}

export function clearBusinessDialogPromptDraft(settingsDraft: BusinessDialogSettings): BusinessDialogSettings {
  return { ...settingsDraft, dialogPrompt: "" };
}

export function resetBusinessSettingsDraft(
  _settingsDraft: BusinessDialogSettings | undefined,
  savedSettings: BusinessDialogSettings | undefined,
): BusinessDialogSettings | undefined {
  return savedSettings ? { ...savedSettings } : undefined;
}

export function isBusinessSettingsDirty(
  savedSettings: BusinessDialogSettings | undefined,
  settingsDraft: BusinessDialogSettings | undefined,
): boolean {
  return Boolean(
    savedSettings &&
      settingsDraft &&
      (savedSettings.assistantDisplayName !== settingsDraft.assistantDisplayName ||
        savedSettings.assistantPrefix !== settingsDraft.assistantPrefix ||
        savedSettings.dialogPrompt !== settingsDraft.dialogPrompt ||
        savedSettings.dialogNotes !== settingsDraft.dialogNotes ||
        savedSettings.invocationPolicy !== settingsDraft.invocationPolicy),
  );
}

export function ChatDetailShell({ token }: { token: string }) {
  const router = useRouter();
  const telegram = useTelegramWebApp();
  const [status, setStatus] = useState<DetailStatus>("loading");
  const [chat, setChat] = useState<BusinessChatDetail>();
  const [history, setHistory] = useState<BusinessHistoryEvent[]>([]);
  const [errorMessage, setErrorMessage] = useState<string>();
  const [actionStatus, setActionStatus] = useState<ActionStatus>(null);
  const [draftPrompt, setDraftPrompt] = useState("");
  const [settings, setSettings] = useState<BusinessDialogSettings>();
  const [settingsDraft, setSettingsDraft] = useState<BusinessDialogSettings>();
  const [settingsStatus, setSettingsStatus] = useState<SettingsStatus>("idle");
  const [settingsErrorMessage, setSettingsErrorMessage] = useState<string>();
  const [settingsActionStatus, setSettingsActionStatus] = useState<ActionStatus>(null);

  const loadDetail = useCallback(async () => {
    if (telegram.status === "missing") {
      setStatus("unauthorized");
      setChat(undefined);
      setHistory([]);
      setSettings(undefined);
      setSettingsDraft(undefined);
      setSettingsStatus("idle");
      return;
    }
    if (telegram.status !== "ready") {
      setStatus("loading");
      return;
    }

    setStatus("loading");
    setSettingsStatus("loading");
    setErrorMessage(undefined);
    setSettingsErrorMessage(undefined);
    setSettingsActionStatus(null);
    try {
      const snapshot = await fetchChatDetailSnapshot(token, telegram.initData);
      setChat(snapshot.chat);
      setHistory(snapshot.history);
      setStatus("ready");
      if (snapshot.settings) {
        setSettings(snapshot.settings);
        setSettingsDraft({ ...snapshot.settings });
        setSettingsStatus("ready");
      } else {
        setSettingsStatus("error");
        setSettingsErrorMessage(snapshot.settingsErrorMessage ?? "settings_unavailable");
      }
    } catch (error) {
      setChat(undefined);
      setHistory([]);
      setSettings(undefined);
      setSettingsDraft(undefined);
      setSettingsErrorMessage(undefined);
      setSettingsStatus("idle");
      setErrorMessage(messageForError(error));
      setStatus(statusForError(error));
    }
  }, [telegram, token]);

  useEffect(() => {
    void Promise.resolve().then(loadDetail);
  }, [loadDetail]);

  const refreshDetailInPlace = useCallback(async (): Promise<BusinessHistoryEvent[] | undefined> => {
    if (telegram.status !== "ready") {
      return;
    }
    try {
      const [detailResponse, historyResponse] = await Promise.all([
        fetchBusinessChatDetail(token, telegram.initData),
        fetchBusinessHistory(token, telegram.initData),
      ]);
      setChat(detailResponse.chat);
      const nextHistory = historyResponse.history ?? detailResponse.history ?? [];
      setHistory(nextHistory);
      setStatus("ready");
      return nextHistory;
    } catch {
      // Keep the current detail mounted; the action status already communicates
      // the draft request result, and a manual Refresh remains available.
      return undefined;
    }
  }, [telegram, token]);

  const waitForGeneratedDraft = useCallback(
    async (knownEventIds: Set<string>, requestStartedAt: number): Promise<BusinessHistoryEvent | undefined> => {
      for (let attempt = 0; attempt < 12; attempt += 1) {
        if (attempt > 0) {
          await new Promise((resolve) => setTimeout(resolve, 1500));
        }
        const nextHistory = await refreshDetailInPlace();
        const generated = nextHistory?.find((event) => {
          if (event.type !== "draft_generated") {
            return false;
          }
          if (event.event_id) {
            return !knownEventIds.has(event.event_id);
          }
          return (event.created_at ?? 0) >= requestStartedAt - 5;
        });
        if (generated) {
          return generated;
        }
        setActionStatus({
          kind: "loading",
          message: "Draft request queued. Waiting for the generated draft to appear below...",
        });
      }
      return undefined;
    },
    [refreshDetailInPlace],
  );

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
      const prompt = draftPrompt.trim();
      const knownEventIds = new Set(history.map((event) => event.event_id).filter((id): id is string => Boolean(id)));
      const requestStartedAt = Date.now() / 1000;
      const response = await generateBusinessDraft(token, telegram.initData, prompt);
      const promptSuffix = prompt ? " Prompt sent with the request." : "";
      setActionStatus({
        kind: "loading",
        message: `Draft ${response.draft.status}. Waiting for the generated draft to appear below...${promptSuffix}`,
      });
      const generated = await waitForGeneratedDraft(knownEventIds, requestStartedAt);
      if (generated) {
        setActionStatus({
          kind: "success",
          message: `Draft generated and added to history below. Approval remains required.${promptSuffix}`,
        });
      } else {
        setActionStatus({
          kind: "success",
          message: `Draft ${response.draft.status}. It is still generating; keep this chat open or tap Refresh in a moment.${promptSuffix}`,
        });
      }
    } catch (error) {
      setActionStatus({ kind: "error", message: messageForError(error) });
    }
  }, [draftPrompt, history, telegram, token, waitForGeneratedDraft]);

  const handleSettingsDraftChange = useCallback((patch: BusinessSettingsPatch) => {
    setSettingsDraft((current) => (current ? { ...current, ...patch } : current));
    setSettingsActionStatus(null);
  }, []);

  const handleClearPrompt = useCallback(() => {
    setSettingsDraft((current) => (current ? clearBusinessDialogPromptDraft(current) : current));
    setSettingsActionStatus(null);
  }, []);

  const handleResetSettings = useCallback(() => {
    setSettingsDraft((current) => resetBusinessSettingsDraft(current, settings));
    setSettingsActionStatus({ kind: "success", message: "Unsaved settings changes discarded." });
  }, [settings]);

  const handleSaveSettings = useCallback(async () => {
    if (telegram.status !== "ready") {
      setSettingsActionStatus({ kind: "error", message: "Open from Telegram to save settings." });
      return;
    }
    if (!settingsDraft) {
      setSettingsActionStatus({ kind: "error", message: "Settings are not loaded yet." });
      return;
    }

    setSettingsActionStatus({ kind: "loading", message: "Saving settings..." });
    try {
      const savedSettings = await saveBusinessChatSettingsSnapshot(token, telegram.initData, settingsDraft);
      setSettings(savedSettings);
      setSettingsDraft({ ...savedSettings });
      setSettingsStatus("ready");
      setSettingsErrorMessage(undefined);
      setSettingsActionStatus({ kind: "success", message: "Settings saved." });
    } catch (error) {
      setSettingsStatus(settings ? "ready" : "error");
      setSettingsActionStatus({ kind: "error", message: messageForError(error) });
    }
  }, [settings, settingsDraft, telegram, token]);

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
      draftPrompt={draftPrompt}
      onDraftPromptChange={setDraftPrompt}
      onGenerateDraft={handleGenerateDraft}
      settings={settings}
      settingsDraft={settingsDraft}
      settingsStatus={settingsStatus}
      settingsErrorMessage={settingsErrorMessage}
      settingsActionStatus={settingsActionStatus}
      settingsDirty={isBusinessSettingsDirty(settings, settingsDraft)}
      onSettingsDraftChange={handleSettingsDraftChange}
      onSaveSettings={handleSaveSettings}
      onClearPrompt={handleClearPrompt}
      onResetSettings={handleResetSettings}
    />
  );
}
