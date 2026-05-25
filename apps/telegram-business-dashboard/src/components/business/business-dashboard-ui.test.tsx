import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { ChatDetailView } from "./chat-detail-view";
import { DashboardView } from "./dashboard-view";
import type { BusinessChatDetail, BusinessChatSummary, BusinessHistoryEvent } from "@/lib/business/types";
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

describe("Business dashboard UI view models", () => {
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
        onBack={vi.fn()}
        onRefresh={vi.fn()}
        onModeChange={vi.fn()}
        onGenerateDraft={vi.fn()}
      />,
    );

    expect(html).toContain("Ada Lovelace");
    expect(html).toContain("Reply allowed");
    expect(html).toContain("Generate draft now");
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
});
