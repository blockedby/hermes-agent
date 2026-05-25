import type { BusinessChatMode, BusinessChatSummary } from "./types";

export type ChatFilter = BusinessChatMode | "all";

export type ChatCounts = Record<ChatFilter, number> & {
  pendingDrafts: number;
  failedDrafts: number;
};

export const CHAT_FILTERS: Array<{ value: ChatFilter; label: string }> = [
  { value: "all", label: "All" },
  { value: "watch", label: "Watch" },
  { value: "draft", label: "Draft" },
  { value: "auto", label: "Auto" },
  { value: "ignored", label: "Ignored" },
];

export const MODE_OPTIONS: Array<{ value: BusinessChatMode; label: string; shortLabel: string }> = [
  { value: "ignored", label: "Ignore", shortLabel: "ignored" },
  { value: "watch", label: "Watch", shortLabel: "watch" },
  { value: "draft", label: "Draft", shortLabel: "draft" },
  { value: "auto", label: "Auto", shortLabel: "auto" },
];

export function countChatsByMode(chats: BusinessChatSummary[]): ChatCounts {
  return chats.reduce<ChatCounts>(
    (counts, chat) => {
      counts.all += 1;
      counts[chat.mode] += 1;
      counts.pendingDrafts += chat.pendingDraftCount;
      counts.failedDrafts += chat.failedDraftCount;
      return counts;
    },
    { all: 0, watch: 0, draft: 0, auto: 0, ignored: 0, pendingDrafts: 0, failedDrafts: 0 },
  );
}

export function filterChats(
  chats: BusinessChatSummary[],
  { mode, query }: { mode: ChatFilter; query: string },
): BusinessChatSummary[] {
  const normalizedQuery = query.trim().toLowerCase();
  return chats.filter((chat) => {
    if (mode !== "all" && chat.mode !== mode) {
      return false;
    }
    if (!normalizedQuery) {
      return true;
    }
    return [chat.displayName, chat.username, chat.lastMessagePreview]
      .filter(Boolean)
      .some((value) => value?.toLowerCase().includes(normalizedQuery));
  });
}

export function relativeTimeLabel(timestampSeconds: number | undefined, nowSeconds = Date.now() / 1000): string {
  if (!timestampSeconds || timestampSeconds <= 0) {
    return "not seen yet";
  }

  const delta = Math.max(0, Math.floor(nowSeconds - timestampSeconds));
  if (delta < 60) {
    return "just now";
  }
  const minutes = Math.floor(delta / 60);
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 48) {
    return `${hours}h ago`;
  }
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function readableEventType(type: string | undefined): string {
  if (!type) {
    return "event";
  }
  return type.replaceAll("_", " ");
}

export function canReplyLabel(canReply: BusinessChatSummary["canReply"]): string {
  switch (canReply) {
    case "yes":
      return "Reply allowed";
    case "no":
      return "Reply disabled";
    default:
      return "Reply unknown";
  }
}
