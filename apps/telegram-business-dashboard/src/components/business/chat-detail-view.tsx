"use client";

import { ArrowLeft, Bot, Clock3, RefreshCw, Send, ShieldAlert, Sparkles } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { BusinessChatDetail, BusinessChatMode, BusinessHistoryEvent } from "@/lib/business/types";
import { MODE_OPTIONS, canReplyLabel, readableEventType, relativeTimeLabel } from "@/lib/business/view-model";
import { cn } from "@/lib/utils";

type DetailStatus = "loading" | "ready" | "error" | "unauthorized" | "not-found";
type ActionStatus = { kind: "success" | "error" | "loading"; message: string } | null;

type ChatDetailViewProps = {
  chat?: BusinessChatDetail;
  history: BusinessHistoryEvent[];
  status: DetailStatus;
  errorMessage?: string;
  actionStatus: ActionStatus;
  nowSeconds?: number;
  onBack: () => void;
  onRefresh: () => void;
  onModeChange: (mode: BusinessChatMode) => void;
  onGenerateDraft: () => void;
};

function modeButtonClass(mode: BusinessChatMode, activeMode?: BusinessChatMode) {
  if (mode !== "auto") {
    return undefined;
  }
  return activeMode === "auto"
    ? "bg-amber-600 text-white hover:bg-amber-600/90"
    : "border-amber-500/40 text-amber-700 dark:text-amber-300";
}

function LoadingDetail() {
  return (
    <div className="space-y-3" aria-label="Loading chat detail">
      <Card>
        <CardContent className="space-y-3 py-5">
          <Skeleton className="h-5 w-44" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
      <Card>
        <CardContent className="space-y-3 py-5">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}

function EmptyOrError({ status, errorMessage, onRefresh }: Pick<ChatDetailViewProps, "status" | "errorMessage" | "onRefresh">) {
  if (status === "unauthorized") {
    return (
      <Alert variant="destructive">
        <ShieldAlert className="size-4" aria-hidden="true" />
        <AlertTitle>Open from Telegram</AlertTitle>
        <AlertDescription>Launch this detail view from the Telegram owner dashboard.</AlertDescription>
      </Alert>
    );
  }

  if (status === "not-found") {
    return (
      <Alert>
        <AlertTitle>Chat not found</AlertTitle>
        <AlertDescription>This Business chat is no longer available in the dashboard.</AlertDescription>
      </Alert>
    );
  }

  return (
    <Alert variant="destructive">
      <AlertTitle>Could not load chat</AlertTitle>
      <AlertDescription className="space-y-3">
        <span className="block">{errorMessage ?? "The Hermes dashboard API is unavailable."}</span>
        <Button variant="outline" size="sm" onClick={onRefresh}>
          Try again
        </Button>
      </AlertDescription>
    </Alert>
  );
}

function HistoryTimeline({ history, nowSeconds }: { history: BusinessHistoryEvent[]; nowSeconds?: number }) {
  if (history.length === 0) {
    return <p className="text-sm text-muted-foreground">No history events recorded yet.</p>;
  }

  return (
    <ol className="space-y-3">
      {history.map((event, index) => (
        <li key={event.event_id ?? `${event.type}-${index}`} className="relative pl-5">
          <span className="absolute left-0 top-1.5 size-2 rounded-full bg-primary" aria-hidden="true" />
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium capitalize">{readableEventType(event.type)}</span>
            {event.mode ? <Badge variant="outline">{event.mode}</Badge> : null}
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Clock3 className="size-3" aria-hidden="true" />
              {relativeTimeLabel(event.created_at, nowSeconds)}
            </span>
          </div>
          {event.preview ? <p className="mt-1 break-words text-sm text-muted-foreground">{event.preview}</p> : null}
        </li>
      ))}
    </ol>
  );
}

export function ChatDetailView({
  chat,
  history,
  status,
  errorMessage,
  actionStatus,
  nowSeconds,
  onBack,
  onRefresh,
  onModeChange,
  onGenerateDraft,
}: ChatDetailViewProps) {
  const isLoading = status === "loading";
  const actionLoading = actionStatus?.kind === "loading";

  return (
    <main className="min-h-dvh bg-background px-3 py-4 text-foreground sm:px-6">
      <section className="mx-auto flex max-w-2xl flex-col gap-4 pb-[env(safe-area-inset-bottom)]">
        <header className="sticky top-0 z-10 -mx-3 border-b bg-background/95 px-3 py-3 backdrop-blur sm:-mx-6 sm:px-6">
          <div className="flex items-center justify-between gap-2">
            <Button variant="ghost" size="sm" onClick={onBack}>
              <ArrowLeft className="size-4" aria-hidden="true" />
              Back
            </Button>
            <Button variant="outline" size="sm" onClick={onRefresh} disabled={isLoading}>
              <RefreshCw className={cn("size-4", isLoading && "animate-spin")} aria-hidden="true" />
              Refresh
            </Button>
          </div>
        </header>

        {isLoading ? <LoadingDetail /> : null}
        {!isLoading && status !== "ready" ? (
          <EmptyOrError status={status} errorMessage={errorMessage} onRefresh={onRefresh} />
        ) : null}

        {!isLoading && status === "ready" && chat ? (
          <>
            <Card>
              <CardHeader>
                <div className="flex min-w-0 items-start justify-between gap-3">
                  <div className="min-w-0">
                    <CardTitle className="truncate text-xl">{chat.displayName || "Unknown customer"}</CardTitle>
                    {chat.username ? <p className="truncate text-sm text-muted-foreground">@{chat.username}</p> : null}
                  </div>
                  <Badge variant="outline" className="shrink-0">
                    {chat.mode}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
                  <div className="rounded-lg border p-3">
                    <div className="text-xs text-muted-foreground">Reply</div>
                    <div className="font-medium">{canReplyLabel(chat.canReply)}</div>
                  </div>
                  <div className="rounded-lg border p-3">
                    <div className="text-xs text-muted-foreground">Pending</div>
                    <div className="font-medium">{chat.pendingDraftCount}</div>
                  </div>
                  <div className="rounded-lg border p-3">
                    <div className="text-xs text-muted-foreground">Failed</div>
                    <div className="font-medium text-destructive">{chat.failedDraftCount}</div>
                  </div>
                  <div className="rounded-lg border p-3">
                    <div className="text-xs text-muted-foreground">Rules</div>
                    <div className="font-medium">{chat.rulesCount}</div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                  <Badge variant="secondary">{relativeTimeLabel(chat.lastSeenAt, nowSeconds)}</Badge>
                  {chat.hasDirectTopic ? <Badge variant="outline">direct topic</Badge> : <Badge variant="outline">no topic</Badge>}
                  {chat.isBot ? <Badge variant="outline">bot chat</Badge> : null}
                </div>

                <div className="space-y-2 rounded-xl border bg-muted/30 p-3">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Bot className="size-4" aria-hidden="true" />
                    Latest preview
                  </div>
                  <p className="break-words text-sm text-muted-foreground">
                    {chat.latestMessage?.preview || chat.lastMessagePreview || "No latest message preview available."}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Mode controls</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4" role="group" aria-label="Change Business chat mode">
                  {MODE_OPTIONS.map((option) => (
                    <Button
                      key={option.value}
                      variant={chat.mode === option.value ? "default" : "outline"}
                      className={modeButtonClass(option.value, chat.mode)}
                      onClick={() => onModeChange(option.value)}
                      disabled={actionLoading || chat.mode === option.value}
                    >
                      {option.label}
                    </Button>
                  ))}
                </div>
                <Button className="w-full" onClick={onGenerateDraft} disabled={actionLoading}>
                  <Send className="size-4" aria-hidden="true" />
                  Generate draft now
                </Button>
                {actionStatus ? (
                  <Alert variant={actionStatus.kind === "error" ? "destructive" : "default"}>
                    <Sparkles className="size-4" aria-hidden="true" />
                    <AlertTitle>{actionStatus.kind === "error" ? "Action failed" : "Action queued"}</AlertTitle>
                    <AlertDescription>{actionStatus.message}</AlertDescription>
                  </Alert>
                ) : null}
                <p className="text-xs text-muted-foreground">
                  Draft generation queues an approval-safe draft and never sends customer text directly.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>History</CardTitle>
              </CardHeader>
              <CardContent>
                <HistoryTimeline history={history} nowSeconds={nowSeconds} />
              </CardContent>
            </Card>
          </>
        ) : null}
      </section>
    </main>
  );
}
