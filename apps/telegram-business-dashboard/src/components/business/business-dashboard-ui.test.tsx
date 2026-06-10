import type * as React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@base-ui/react/button", () => ({
  Button: ({ className, ...props }: React.ComponentProps<"button">) => <button className={className} {...props} />,
}));

vi.mock("@base-ui/react/merge-props", () => ({
  mergeProps: (...props: Array<Record<string, unknown>>) => Object.assign({}, ...props),
}));

vi.mock("@base-ui/react/use-render", () => ({
  useRender: ({ defaultTagName, props }: { defaultTagName: keyof React.JSX.IntrinsicElements; props: Record<string, unknown> }) => {
    const Tag = defaultTagName;
    return <Tag {...props} />;
  },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/lib/telegram/use-telegram-webapp", () => ({
  useTelegramWebApp: () => ({ status: "ready", initData: "query_id=test&hash=signed" }),
}));

vi.mock("@/lib/business/api", () => {
  class BusinessApiError extends Error {
    status: number;
    code: string;

    constructor(status: number, code: string, message = code) {
      super(message);
      this.status = status;
      this.code = code;
    }
  }

  return {
    BusinessApiError,
    fetchBusinessChatDetail: vi.fn(),
    fetchBusinessHistory: vi.fn(),
    fetchBusinessChatSettings: vi.fn(),
    updateBusinessChatMode: vi.fn(),
    generateBusinessDraft: vi.fn(),
    updateBusinessChatSettings: vi.fn(),
  };
});

import { ChatDetailView } from "./chat-detail-view";
import {
  clearBusinessDialogPromptDraft,
  fetchChatDetailSnapshot,
  isBusinessSettingsDirty,
  resetBusinessSettingsDraft,
  saveBusinessChatSettingsSnapshot,
} from "./chat-detail-shell";
import { DashboardView } from "./dashboard-view";
import {
  BusinessApiError,
  fetchBusinessChatDetail,
  fetchBusinessChatSettings,
  fetchBusinessHistory,
  updateBusinessChatSettings,
} from "@/lib/business/api";
import type { BusinessChatDetail, BusinessChatSummary, BusinessDialogSettings, BusinessHistoryEvent } from "@/lib/business/types";
import { countChatsByMode, filterChats, relativeTimeLabel } from "@/lib/business/view-model";

const chats: BusinessChatSummary[] = [
  {
    token: "tok-watch",
    displayName: "Ada Lovelace",
    username: "ada",
    mode: "watch",
    lastSeenAt: 1_800_000,
    lastMessagePreview: "Can you help me with the shipment timeline?",
    canReply: "yes",
    pendingDraftCount: 2,
    failedDraftCount: 0,
    rulesCount: 1,
    hasDirectTopic: true,
  },
  {
    token: "tok-auto",
    displayName: "Very Long Customer Name That Should Wrap Safely On Mobile Screens",
    mode: "auto",
    lastSeenAt: 1_740_000,
    lastMessagePreview: "A very long customer message preview that should never force horizontal overflow in the card layout.",
    canReply: "unknown",
    pendingDraftCount: 0,
    failedDraftCount: 1,
    rulesCount: 0,
    hasDirectTopic: false,
  },
];

const detail: BusinessChatDetail = {
  ...chats[0],
  latestMessage: {
    preview: "Latest customer question about the shipment timeline.",
    hasText: true,
    hasMessageId: true,
  },
  lastDashboardDraftStatus: "queued",
};

const history: BusinessHistoryEvent[] = [
  {
    event_id: "evt-1",
    created_at: 1_800_000,
    type: "draft_requested",
    preview: "Owner requested a fresh draft.",
    mode: "draft",
  },
  {
    event_id: "evt-2",
    created_at: 1_700_000,
    type: "inbound",
    preview: "Customer asked for a shipping update.",
  },
];

const settings: BusinessDialogSettings = {
  assistantDisplayName: "Hermes Concierge",
  assistantPrefix: "🤖 Hermes:",
  dialogPrompt: "Be concise and ask one clarifying question when shipping dates are unclear.",
  dialogNotes: "VIP customer who prefers short answers.",
  invocationPolicy: "mention_draft",
  updatedAt: 1_790_000,
  updatedByUserId: "owner-42",
};

const changedSettings: BusinessDialogSettings = {
  ...settings,
  assistantDisplayName: "Hermes Support",
  dialogPrompt: "Updated owner prompt.",
  invocationPolicy: "mention_direct",
};

describe("Business dashboard UI view models", () => {
  beforeEach(() => {
    vi.mocked(fetchBusinessChatDetail).mockReset();
    vi.mocked(fetchBusinessHistory).mockReset();
    vi.mocked(fetchBusinessChatSettings).mockReset();
    vi.mocked(updateBusinessChatSettings).mockReset();
  });
  it("filters chats and counts visible mode/draft badges", () => {
    expect(filterChats(chats, { mode: "all", query: "ada" })).toHaveLength(1);
    expect(filterChats(chats, { mode: "auto", query: "" })).toHaveLength(1);
    expect(filterChats(chats, { mode: "ignored", query: "" })).toEqual([]);

    expect(countChatsByMode(chats)).toEqual({
      all: 2,
      watch: 1,
      draft: 0,
      auto: 1,
      ignored: 0,
      pendingDrafts: 2,
      failedDrafts: 1,
    });
    expect(relativeTimeLabel(1_800_000, 1_800_000)).toBe("just now");
  });

  it("renders mobile-first dashboard cards, counts, filters, and state copy", () => {
    const html = renderToStaticMarkup(
      <DashboardView
        chats={chats}
        filter="all"
        query=""
        nowSeconds={1_800_000}
        status="ready"
        onFilterChange={vi.fn()}
        onQueryChange={vi.fn()}
        onRefresh={vi.fn()}
      />,
    );

    expect(html).toContain("Business");
    expect(html).toContain("Refresh");
    expect(html).toContain("Pending drafts");
    expect(html).toContain("Ada Lovelace");
    expect(html).toContain("@ada");
    expect(html).toContain("watch");
    expect(html).toContain("auto");
    expect(html).toContain("2 pending");
    expect(html).toContain("1 failed");
    expect(html).toContain("Can you help me with the shipment timeline?");
  });

  it("renders empty, loading, error, and unauthorized dashboard states", () => {
    const loading = renderToStaticMarkup(
      <DashboardView
        chats={[]}
        filter="all"
        query=""
        status="loading"
        onFilterChange={vi.fn()}
        onQueryChange={vi.fn()}
        onRefresh={vi.fn()}
      />,
    );
    expect(loading).toContain("Loading business chats");

    const empty = renderToStaticMarkup(
      <DashboardView
        chats={[]}
        filter="all"
        query=""
        status="ready"
        onFilterChange={vi.fn()}
        onQueryChange={vi.fn()}
        onRefresh={vi.fn()}
      />,
    );
    expect(empty).toContain("No Business chats yet");

    const error = renderToStaticMarkup(
      <DashboardView
        chats={[]}
        filter="all"
        query=""
        status="error"
        errorMessage="dashboard_unavailable"
        onFilterChange={vi.fn()}
        onQueryChange={vi.fn()}
        onRefresh={vi.fn()}
      />,
    );
    expect(error).toContain("Could not load dashboard");
    expect(error).toContain("dashboard_unavailable");

    const unauthorized = renderToStaticMarkup(
      <DashboardView
        chats={[]}
        filter="all"
        query=""
        status="unauthorized"
        onFilterChange={vi.fn()}
        onQueryChange={vi.fn()}
        onRefresh={vi.fn()}
      />,
    );
    expect(unauthorized).toContain("Open from Telegram");
  });

  it("renders detail controls, draft action, latest preview, and history timeline", () => {
    const html = renderToStaticMarkup(
      <ChatDetailView
        chat={detail}
        history={history}
        nowSeconds={1_800_000}
        status="ready"
        actionStatus={null}
        draftPrompt="mention warranty"
        onBack={vi.fn()}
        onRefresh={vi.fn()}
        onModeChange={vi.fn()}
        onDraftPromptChange={vi.fn()}
        onGenerateDraft={vi.fn()}
      />,
    );

    expect(html).toContain("Ada Lovelace");
    expect(html).toContain("Reply allowed");
    expect(html).toContain("Generate draft now");
    expect(html).toContain("Optional draft topic");
    expect(html).toContain("mention warranty");
    expect(html).toContain("Ignore");
    expect(html).toContain("Watch");
    expect(html).toContain("Draft");
    expect(html).toContain("Auto");
    expect(html).toContain("Latest preview");
    expect(html).toContain("Latest customer question");
    expect(html).toContain("History");
    expect(html).toContain("draft requested");
    expect(html).toContain("Owner requested a fresh draft.");
  });

  it("renders dialog settings controls without replacing existing mode and draft controls", () => {
    const html = renderToStaticMarkup(
      <ChatDetailView
        chat={detail}
        history={history}
        nowSeconds={1_800_000}
        status="ready"
        actionStatus={null}
        draftPrompt="mention warranty"
        settings={settings}
        settingsDraft={changedSettings}
        settingsStatus="ready"
        settingsActionStatus={{ kind: "success", message: "Settings saved." }}
        onBack={vi.fn()}
        onRefresh={vi.fn()}
        onModeChange={vi.fn()}
        onDraftPromptChange={vi.fn()}
        onGenerateDraft={vi.fn()}
        onSettingsDraftChange={vi.fn()}
        onSaveSettings={vi.fn()}
        onClearPrompt={vi.fn()}
        onResetSettings={vi.fn()}
      />,
    );

    expect(html).toContain("Dialog settings");
    expect(html).toContain("Assistant display name");
    expect(html).toContain("Hermes Support");
    expect(html).toContain("Assistant prefix");
    expect(html).toContain("🤖 Hermes:");
    expect(html).toContain("Dialog prompt");
    expect(html).toContain("Updated owner prompt.");
    expect(html).toContain("Private owner notes");
    expect(html).toContain("VIP customer who prefers short answers.");
    expect(html).toContain("Invocation policy");
    expect(html).toContain("Save settings");
    expect(html).toContain("Clear prompt");
    expect(html).toContain("Reset changes");
    expect(html).toContain("Settings saved.");
    expect(html).toContain("Generate draft now");
    expect(html).toContain("Optional draft topic");
  });

  it("renders settings validation errors non-destructively with chat detail controls still visible", () => {
    const html = renderToStaticMarkup(
      <ChatDetailView
        chat={detail}
        history={history}
        status="ready"
        actionStatus={null}
        settings={settings}
        settingsDraft={changedSettings}
        settingsStatus="error"
        settingsErrorMessage="invalid_invocation_policy"
        settingsActionStatus={{ kind: "error", message: "invalid_settings" }}
        onBack={vi.fn()}
        onRefresh={vi.fn()}
        onModeChange={vi.fn()}
        onGenerateDraft={vi.fn()}
        onSettingsDraftChange={vi.fn()}
        onSaveSettings={vi.fn()}
        onClearPrompt={vi.fn()}
        onResetSettings={vi.fn()}
      />,
    );

    expect(html).toContain("Settings issue");
    expect(html).toContain("invalid_invocation_policy");
    expect(html).toContain("Settings update failed");
    expect(html).toContain("invalid_settings");
    expect(html).toContain("Mode controls");
    expect(html).toContain("Generate draft now");
    expect(html).toContain("Latest preview");
  });

  it("loads settings for the selected chat while preserving detail when settings fail", async () => {
    vi.mocked(fetchBusinessChatDetail).mockResolvedValue({ chat: detail });
    vi.mocked(fetchBusinessHistory).mockResolvedValue({ chatToken: "tok-watch", history, nextCursor: null, count: history.length });
    vi.mocked(fetchBusinessChatSettings).mockResolvedValue({ settings });

    await expect(fetchChatDetailSnapshot("tok-watch", "init-data")).resolves.toEqual({
      chat: detail,
      history,
      settings,
    });
    expect(fetchBusinessChatSettings).toHaveBeenCalledWith("tok-watch", "init-data");

    vi.mocked(fetchBusinessChatSettings).mockRejectedValueOnce(new BusinessApiError(400, "invalid_settings"));
    await expect(fetchChatDetailSnapshot("tok-watch", "init-data")).resolves.toMatchObject({
      chat: detail,
      history,
      settingsErrorMessage: "invalid_settings",
    });
  });

  it("saves settings through the settings route and supports clear/reset local draft helpers", async () => {
    vi.mocked(updateBusinessChatSettings).mockResolvedValue({ settings: changedSettings });

    await expect(saveBusinessChatSettingsSnapshot("tok-watch", "init-data", changedSettings)).resolves.toEqual(changedSettings);
    expect(updateBusinessChatSettings).toHaveBeenCalledWith("tok-watch", "init-data", changedSettings);

    expect(clearBusinessDialogPromptDraft(changedSettings)).toEqual({
      ...changedSettings,
      dialogPrompt: "",
    });
    expect(clearBusinessDialogPromptDraft(changedSettings).dialogNotes).toBe(changedSettings.dialogNotes);
    expect(resetBusinessSettingsDraft(changedSettings, settings)).toEqual(settings);
    expect(isBusinessSettingsDirty(settings, changedSettings)).toBe(true);
    expect(isBusinessSettingsDirty(settings, settings)).toBe(false);
  });
});
