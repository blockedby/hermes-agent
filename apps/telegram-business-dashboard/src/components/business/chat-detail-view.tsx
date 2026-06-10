"use client";

import { ArrowLeft, Bot, Clock3, Eraser, RefreshCw, RotateCcw, Save, Send, Settings2, ShieldAlert, Sparkles } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  BusinessChatDetail,
  BusinessChatMode,
  BusinessDialogSettings,
  BusinessHistoryEvent,
  BusinessInvocationPolicy,
  BusinessSettingsPatch,
} from "@/lib/business/types";
import { MODE_OPTIONS, canReplyLabel, readableEventType, relativeTimeLabel } from "@/lib/business/view-model";
import { cn } from "@/lib/utils";

type DetailStatus = "loading" | "ready" | "error" | "unauthorized" | "not-found";
type SettingsStatus = "idle" | "loading" | "ready" | "error";
type ActionStatus = { kind: "success" | "error" | "loading"; message: string } | null;

type ChatDetailViewProps = {
  chat?: BusinessChatDetail;
  history: BusinessHistoryEvent[];
  status: DetailStatus;
  errorMessage?: string;
  actionStatus: ActionStatus;
  draftPrompt?: string;
  settings?: BusinessDialogSettings;
  settingsDraft?: BusinessDialogSettings;
  settingsStatus?: SettingsStatus;
  settingsErrorMessage?: string;
  settingsActionStatus?: ActionStatus;
  settingsDirty?: boolean;
  nowSeconds?: number;
  onBack: () => void;
  onRefresh: () => void;
  onModeChange: (mode: BusinessChatMode) => void;
  onDraftPromptChange?: (prompt: string) => void;
  onGenerateDraft: () => void;
  onSettingsDraftChange?: (patch: BusinessSettingsPatch) => void;
  onSaveSettings?: () => void;
  onClearPrompt?: () => void;
  onResetSettings?: () => void;
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
        <Button type="button" variant="outline" size="sm" onClick={onRefresh}>
          Try again
        </Button>
      </AlertDescription>
    </Alert>
  );
}

const INVOCATION_POLICY_OPTIONS: Array<{ value: BusinessInvocationPolicy; label: string; help: string }> = [
  { value: "off", label: "Off", help: "Hermes follows the selected mode without mention-only invocation." },
  { value: "mention_draft", label: "Mention creates draft", help: "Mentioning Hermes queues an approval-safe draft." },
  { value: "mention_direct", label: "Mention may send direct", help: "Mentioning Hermes can use direct-send behavior when the chat mode allows it." },
];

const inputClassName =
  "h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50";
const textareaClassName =
  "min-h-24 w-full resize-y rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50";

function ChatSettingsCard({
  settings,
  settingsDraft,
  settingsStatus = "idle",
  settingsErrorMessage,
  settingsActionStatus,
  settingsDirty = false,
  onSettingsDraftChange,
  onSaveSettings,
  onClearPrompt,
  onResetSettings,
}: Pick<
  ChatDetailViewProps,
  | "settings"
  | "settingsDraft"
  | "settingsStatus"
  | "settingsErrorMessage"
  | "settingsActionStatus"
  | "settingsDirty"
  | "onSettingsDraftChange"
  | "onSaveSettings"
  | "onClearPrompt"
  | "onResetSettings"
>) {
  const draft = settingsDraft ?? settings;
  const settingsLoading = settingsStatus === "loading" || settingsActionStatus?.kind === "loading";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings2 className="size-4" aria-hidden="true" />
          Dialog settings
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Tune the assistant identity and owner-only context for this Business dialog. These settings do not replace mode or draft controls.
        </p>

        {settingsStatus === "loading" && !draft ? (
          <div className="space-y-3" aria-label="Loading dialog settings">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-10 w-40" />
          </div>
        ) : null}

        {settingsStatus === "error" ? (
          <Alert variant={draft ? "default" : "destructive"}>
            <AlertTitle>Settings issue</AlertTitle>
            <AlertDescription>{settingsErrorMessage ?? "Could not load dialog settings."}</AlertDescription>
          </Alert>
        ) : null}

        {draft ? (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-2">
                <label htmlFor="business-assistant-display-name" className="text-sm font-medium">
                  Assistant display name
                </label>
                <input
                  id="business-assistant-display-name"
                  className={inputClassName}
                  value={draft.assistantDisplayName}
                  onChange={(event) => onSettingsDraftChange?.({ assistantDisplayName: event.target.value })}
                  disabled={settingsLoading}
                  maxLength={80}
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="business-assistant-prefix" className="text-sm font-medium">
                  Assistant prefix
                </label>
                <input
                  id="business-assistant-prefix"
                  className={inputClassName}
                  value={draft.assistantPrefix}
                  onChange={(event) => onSettingsDraftChange?.({ assistantPrefix: event.target.value })}
                  disabled={settingsLoading}
                  maxLength={80}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <label htmlFor="business-dialog-prompt" className="text-sm font-medium">
                  Dialog prompt
                </label>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={onClearPrompt}
                  disabled={settingsLoading || draft.dialogPrompt.length === 0}
                >
                  <Eraser className="size-4" aria-hidden="true" />
                  Clear prompt
                </Button>
              </div>
              <textarea
                id="business-dialog-prompt"
                className={textareaClassName}
                value={draft.dialogPrompt}
                onChange={(event) => onSettingsDraftChange?.({ dialogPrompt: event.target.value })}
                placeholder="Owner-only instructions for this customer dialog"
                disabled={settingsLoading}
                maxLength={4000}
              />
              <p className="text-xs text-muted-foreground">Clearing this field does not clear the name, prefix, notes, or invocation policy.</p>
            </div>

            <div className="space-y-2">
              <label htmlFor="business-dialog-notes" className="text-sm font-medium">
                Private owner notes
              </label>
              <textarea
                id="business-dialog-notes"
                className={textareaClassName}
                value={draft.dialogNotes}
                onChange={(event) => onSettingsDraftChange?.({ dialogNotes: event.target.value })}
                placeholder="Private context for the business owner; not a customer-facing message"
                disabled={settingsLoading}
                maxLength={4000}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="business-invocation-policy" className="text-sm font-medium">
                Invocation policy
              </label>
              <select
                id="business-invocation-policy"
                className={inputClassName}
                value={draft.invocationPolicy}
                onChange={(event) => onSettingsDraftChange?.({ invocationPolicy: event.target.value as BusinessInvocationPolicy })}
                disabled={settingsLoading}
              >
                {INVOCATION_POLICY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground">
                {INVOCATION_POLICY_OPTIONS.find((option) => option.value === draft.invocationPolicy)?.help}
              </p>
            </div>

            <div className="flex flex-col gap-2 sm:flex-row">
              <Button type="button" className="sm:flex-1" onClick={onSaveSettings} disabled={settingsLoading || !settingsDirty}>
                <Save className="size-4" aria-hidden="true" />
                {settingsActionStatus?.kind === "loading" ? "Saving settings..." : "Save settings"}
              </Button>
              <Button type="button" variant="outline" className="sm:flex-1" onClick={onResetSettings} disabled={settingsLoading || !settingsDirty}>
                <RotateCcw className="size-4" aria-hidden="true" />
                Reset changes
              </Button>
            </div>

            {settingsActionStatus ? (
              <Alert variant={settingsActionStatus.kind === "error" ? "destructive" : "default"}>
                <Sparkles className="size-4" aria-hidden="true" />
                <AlertTitle>{settingsActionStatus.kind === "error" ? "Settings update failed" : settingsActionStatus.kind === "loading" ? "Saving settings" : "Settings saved"}</AlertTitle>
                <AlertDescription>{settingsActionStatus.message}</AlertDescription>
              </Alert>
            ) : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
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
  draftPrompt = "",
  settings,
  settingsDraft,
  settingsStatus,
  settingsErrorMessage,
  settingsActionStatus,
  settingsDirty,
  nowSeconds,
  onBack,
  onRefresh,
  onModeChange,
  onDraftPromptChange,
  onGenerateDraft,
  onSettingsDraftChange,
  onSaveSettings,
  onClearPrompt,
  onResetSettings,
}: ChatDetailViewProps) {
  const isLoading = status === "loading";
  const actionLoading = actionStatus?.kind === "loading";

  return (
    <main className="min-h-dvh bg-background px-3 py-4 text-foreground sm:px-6">
      <section className="mx-auto flex max-w-2xl flex-col gap-4 pb-[env(safe-area-inset-bottom)]">
        <header className="sticky top-0 z-10 -mx-3 border-b bg-background/95 px-3 py-3 backdrop-blur sm:-mx-6 sm:px-6">
          <div className="flex items-center justify-between gap-2">
            <Button type="button" variant="ghost" size="sm" onClick={onBack}>
              <ArrowLeft className="size-4" aria-hidden="true" />
              Back
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={onRefresh} disabled={isLoading}>
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
                      type="button"
                      variant={chat.mode === option.value ? "default" : "outline"}
                      className={modeButtonClass(option.value, chat.mode)}
                      onClick={() => onModeChange(option.value)}
                      disabled={actionLoading || chat.mode === option.value}
                    >
                      {option.label}
                    </Button>
                  ))}
                </div>
                <div className="space-y-2">
                  <label htmlFor="business-draft-prompt" className="text-sm font-medium">
                    Optional draft topic
                  </label>
                  <input
                    id="business-draft-prompt"
                    className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50"
                    value={draftPrompt}
                    onChange={(event) => onDraftPromptChange?.(event.target.value)}
                    placeholder="Optional: ask Hermes to focus the draft on a theme or answer angle"
                    disabled={actionLoading}
                  />
                  <p className="text-xs text-muted-foreground">Leave empty to draft from the latest customer message.</p>
                </div>
                <Button type="button" className="w-full" onClick={onGenerateDraft} disabled={actionLoading}>
                  <Send className="size-4" aria-hidden="true" />
                  {actionLoading ? "Queueing draft..." : "Generate draft now"}
                </Button>
                {actionStatus ? (
                  <Alert variant={actionStatus.kind === "error" ? "destructive" : "default"}>
                    <Sparkles className="size-4" aria-hidden="true" />
                    <AlertTitle>{actionStatus.kind === "error" ? "Action failed" : actionStatus.kind === "loading" ? "Generating draft" : "Draft request queued"}</AlertTitle>
                    <AlertDescription>{actionStatus.message}</AlertDescription>
                  </Alert>
                ) : null}
                <p className="text-xs text-muted-foreground">
                  Draft generation queues an approval-safe draft and never sends customer text directly.
                </p>
              </CardContent>
            </Card>

            <ChatSettingsCard
              settings={settings}
              settingsDraft={settingsDraft}
              settingsStatus={settingsStatus}
              settingsErrorMessage={settingsErrorMessage}
              settingsActionStatus={settingsActionStatus}
              settingsDirty={settingsDirty}
              onSettingsDraftChange={onSettingsDraftChange}
              onSaveSettings={onSaveSettings}
              onClearPrompt={onClearPrompt}
              onResetSettings={onResetSettings}
            />

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
