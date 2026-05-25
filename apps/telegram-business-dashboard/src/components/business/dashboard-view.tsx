"use client";

import { AlertCircle, Clock3, MessageCircle, RefreshCw, Search, ShieldAlert, Sparkles } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { BusinessChatSummary } from "@/lib/business/types";
import {
  CHAT_FILTERS,
  type ChatFilter,
  countChatsByMode,
  filterChats,
  relativeTimeLabel,
} from "@/lib/business/view-model";
import { cn } from "@/lib/utils";

type DashboardStatus = "loading" | "ready" | "error" | "unauthorized";

type DashboardViewProps = {
  chats: BusinessChatSummary[];
  filter: ChatFilter;
  query: string;
  status: DashboardStatus;
  errorMessage?: string;
  nowSeconds?: number;
  onFilterChange: (filter: ChatFilter) => void;
  onQueryChange: (query: string) => void;
  onRefresh: () => void;
};

function modeBadgeClass(mode: BusinessChatSummary["mode"]): string {
  switch (mode) {
    case "auto":
      return "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300";
    case "draft":
      return "border-blue-500/40 bg-blue-500/10 text-blue-700 dark:text-blue-300";
    case "watch":
      return "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300";
    case "ignored":
      return "border-muted-foreground/30 bg-muted text-muted-foreground";
  }
}

function CountCard({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-xl border bg-card p-3 shadow-sm">
      <div className="text-[0.7rem] font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className={cn("mt-1 text-2xl font-semibold tabular-nums", tone)}>{value}</div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-3" aria-label="Loading business chats">
      {Array.from({ length: 3 }).map((_, index) => (
        <Card key={index}>
          <CardContent className="space-y-3">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function StateCard({ status, errorMessage, onRefresh }: Pick<DashboardViewProps, "status" | "errorMessage" | "onRefresh">) {
  if (status === "unauthorized") {
    return (
      <Alert variant="destructive">
        <ShieldAlert className="size-4" aria-hidden="true" />
        <AlertTitle>Open from Telegram</AlertTitle>
        <AlertDescription>
          Launch this dashboard from the Telegram bot with an allowed owner account.
        </AlertDescription>
      </Alert>
    );
  }

  if (status === "error") {
    return (
      <Alert variant="destructive">
        <AlertCircle className="size-4" aria-hidden="true" />
        <AlertTitle>Could not load dashboard</AlertTitle>
        <AlertDescription className="space-y-3">
          <span className="block">{errorMessage ?? "The Hermes dashboard API is unavailable."}</span>
          <Button variant="outline" size="sm" onClick={onRefresh}>
            Try again
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-3 py-8 text-center">
        <MessageCircle className="size-9 text-muted-foreground" aria-hidden="true" />
        <div>
          <h2 className="font-medium">No Business chats yet</h2>
          <p className="text-sm text-muted-foreground">
            New Telegram Business conversations will appear here after Hermes records them.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={onRefresh}>
          Refresh
        </Button>
      </CardContent>
    </Card>
  );
}

function ChatCard({ chat, nowSeconds }: { chat: BusinessChatSummary; nowSeconds?: number }) {
  return (
    <a
      href={`/chats/${encodeURIComponent(chat.token)}`}
      className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <Card className="transition hover:bg-muted/30">
        <CardHeader className="gap-2">
          <div className="flex min-w-0 items-start justify-between gap-3">
            <div className="min-w-0">
              <CardTitle className="truncate">{chat.displayName || "Unknown customer"}</CardTitle>
              {chat.username ? <p className="truncate text-xs text-muted-foreground">@{chat.username}</p> : null}
            </div>
            <Badge variant="outline" className={cn("shrink-0", modeBadgeClass(chat.mode))}>
              {chat.mode}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="line-clamp-2 break-words text-sm text-muted-foreground">
            {chat.lastMessagePreview || "No message preview available."}
          </p>
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <Clock3 className="size-3" aria-hidden="true" />
              {relativeTimeLabel(chat.lastSeenAt, nowSeconds)}
            </span>
            <Badge variant="secondary">{chat.canReply === "yes" ? "can reply" : `reply ${chat.canReply}`}</Badge>
            {chat.pendingDraftCount > 0 ? (
              <Badge variant="outline" className="border-blue-500/40 text-blue-700 dark:text-blue-300">
                {chat.pendingDraftCount} pending
              </Badge>
            ) : null}
            {chat.failedDraftCount > 0 ? (
              <Badge variant="destructive">{chat.failedDraftCount} failed</Badge>
            ) : null}
          </div>
        </CardContent>
      </Card>
    </a>
  );
}

export function DashboardView({
  chats,
  filter,
  query,
  status,
  errorMessage,
  nowSeconds,
  onFilterChange,
  onQueryChange,
  onRefresh,
}: DashboardViewProps) {
  const counts = countChatsByMode(chats);
  const visibleChats = filterChats(chats, { mode: filter, query });
  const isLoading = status === "loading";

  return (
    <main className="min-h-dvh bg-background px-3 py-4 text-foreground sm:px-6">
      <section className="mx-auto flex max-w-2xl flex-col gap-4 pb-[env(safe-area-inset-bottom)]">
        <header className="sticky top-0 z-10 -mx-3 border-b bg-background/95 px-3 py-3 backdrop-blur sm:-mx-6 sm:px-6">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <Badge variant="outline" className="mb-2">
                Telegram Business
              </Badge>
              <h1 className="truncate text-2xl font-semibold tracking-tight">Business</h1>
              <p className="text-sm text-muted-foreground">Owner dashboard for replies, drafts, and modes.</p>
            </div>
            <Button variant="outline" size="sm" onClick={onRefresh} disabled={isLoading}>
              <RefreshCw className={cn("size-4", isLoading && "animate-spin")} aria-hidden="true" />
              Refresh
            </Button>
          </div>
        </header>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <CountCard label="All" value={counts.all} />
          <CountCard label="Watch" value={counts.watch} />
          <CountCard label="Draft" value={counts.draft} />
          <CountCard label="Auto" value={counts.auto} tone="text-amber-600 dark:text-amber-300" />
          <CountCard label="Ignored" value={counts.ignored} />
          <CountCard label="Pending drafts" value={counts.pendingDrafts} tone="text-blue-600 dark:text-blue-300" />
          <CountCard label="Failed drafts" value={counts.failedDrafts} tone="text-destructive" />
        </div>

        <Card>
          <CardContent className="space-y-3">
            <label className="relative block">
              <span className="sr-only">Search chats</span>
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <input
                value={query}
                onChange={(event) => onQueryChange(event.currentTarget.value)}
                placeholder="Search chats or previews"
                className="h-10 w-full rounded-lg border bg-background pl-9 pr-3 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
            <div className="flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label="Filter chats by mode">
              {CHAT_FILTERS.map((item) => (
                <Button
                  key={item.value}
                  type="button"
                  variant={filter === item.value ? "default" : "outline"}
                  size="sm"
                  role="tab"
                  aria-selected={filter === item.value}
                  onClick={() => onFilterChange(item.value)}
                >
                  {item.label}
                  <span className="text-xs opacity-75">{counts[item.value]}</span>
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {status === "loading" ? <DashboardSkeleton /> : null}
        {status === "ready" && visibleChats.length > 0 ? (
          <div className="space-y-3" aria-live="polite">
            {visibleChats.map((chat) => (
              <ChatCard key={chat.token} chat={chat} nowSeconds={nowSeconds} />
            ))}
          </div>
        ) : null}
        {status !== "loading" && (status !== "ready" || visibleChats.length === 0) ? (
          <StateCard status={status} errorMessage={errorMessage} onRefresh={onRefresh} />
        ) : null}

        <p className="flex items-center gap-2 px-1 text-xs text-muted-foreground">
          <Sparkles className="size-3" aria-hidden="true" />
          Generate draft now queues approval-safe drafts; it does not send directly to customers.
        </p>
      </section>
    </main>
  );
}
