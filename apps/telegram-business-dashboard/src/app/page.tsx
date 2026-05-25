"use client";

import { useEffect, useState } from "react";
import { LockKeyhole, ShieldCheck } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { useTelegramWebApp } from "@/lib/telegram/use-telegram-webapp";

type SessionState =
  | { status: "idle" }
  | { status: "checking" }
  | { status: "admin"; name?: string }
  | { status: "forbidden" }
  | { status: "error"; message: string };

type SessionResponse = {
  ok: boolean;
  error?: string;
  user?: {
    telegramUserId: number;
    username?: string;
    firstName?: string;
  };
};

export default function HomePage() {
  const telegram = useTelegramWebApp();
  const [session, setSession] = useState<SessionState>({ status: "idle" });

  useEffect(() => {
    if (telegram.status !== "ready") {
      return;
    }

    let cancelled = false;

    Promise.resolve()
      .then(() => {
        setSession({ status: "checking" });
        return fetch("/api/session", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ initData: telegram.initData }),
        });
      })
      .then(async (response) => {
        const payload = (await response.json()) as SessionResponse;
        if (cancelled) {
          return;
        }
        if (response.status === 403) {
          setSession({ status: "forbidden" });
          return;
        }
        if (!response.ok || !payload.ok) {
          throw new Error(payload.error ?? "Telegram session validation failed");
        }
        setSession({
          status: "admin",
          name: payload.user?.firstName ?? payload.user?.username,
        });
      })
      .catch((error: Error) => {
        if (!cancelled) {
          setSession({ status: "error", message: error.message });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [telegram]);

  const isLoading = telegram.status === "loading" || session.status === "checking";

  return (
    <main className="min-h-dvh bg-background px-4 py-6 text-foreground">
      <section className="mx-auto flex min-h-[calc(100dvh-3rem)] max-w-xl flex-col justify-center gap-4">
        <div className="space-y-2 text-center">
          <Badge variant="outline" className="mx-auto">
            Telegram Web App
          </Badge>
          <h1 className="text-2xl font-semibold tracking-tight">Hermes Business</h1>
          <p className="text-sm text-muted-foreground">
            Minimal owner dashboard shell. Chat data wiring comes next.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="size-5 text-primary" aria-hidden="true" />
              Admin session
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading && (
              <div className="space-y-3" aria-label="Checking Telegram session">
                <Skeleton className="h-5 w-44" />
                <Skeleton className="h-20 w-full" />
              </div>
            )}

            {telegram.status === "missing" && (
              <Alert>
                <LockKeyhole className="size-4" aria-hidden="true" />
                <AlertTitle>Open from Telegram</AlertTitle>
                <AlertDescription>
                  This dashboard is available only when launched as a Telegram Web App.
                </AlertDescription>
              </Alert>
            )}

            {session.status === "forbidden" && (
              <Alert variant="destructive">
                <LockKeyhole className="size-4" aria-hidden="true" />
                <AlertTitle>Admin only</AlertTitle>
                <AlertDescription>
                  Your Telegram account is not allowed to access this dashboard.
                </AlertDescription>
              </Alert>
            )}

            {session.status === "error" && (
              <Alert variant="destructive">
                <AlertTitle>Authorization failed</AlertTitle>
                <AlertDescription>{session.message}</AlertDescription>
              </Alert>
            )}

            {session.status === "admin" && (
              <Alert>
                <ShieldCheck className="size-4" aria-hidden="true" />
                <AlertTitle>Admin verified{session.name ? `: ${session.name}` : ""}</AlertTitle>
                <AlertDescription>
                  The dashboard shell is ready. Business chat list, history, and draft actions
                  will be added in the following tasks.
                </AlertDescription>
              </Alert>
            )}

            <Separator />

            <div className="grid grid-cols-3 gap-2 text-center text-xs text-muted-foreground">
              <div className="rounded-lg border p-2">
                <div className="font-medium text-foreground">Chats</div>
                <div>Next task</div>
              </div>
              <div className="rounded-lg border p-2">
                <div className="font-medium text-foreground">Drafts</div>
                <div>Approval-safe</div>
              </div>
              <div className="rounded-lg border p-2">
                <div className="font-medium text-foreground">History</div>
                <div>Bounded</div>
              </div>
            </div>

            <Button className="w-full" disabled>
              Business data wiring pending
            </Button>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
