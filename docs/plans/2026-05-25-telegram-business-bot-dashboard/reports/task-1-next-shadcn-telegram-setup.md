# Task 1 expanded setup instructions: Next.js + shadcn Telegram Web App

Date: 2026-05-25
Parent issue: https://github.com/blockedby/hermes-agent/issues/19
Sub-issue: https://github.com/blockedby/hermes-agent/issues/21
Scope: `apps/telegram-business-dashboard/` skeleton, Telegram Web App config, admin-only auth foundation, Vercel deployment config, and VPS proxy notes.

## Research inputs

- Subagent research on current Next.js/shadcn/Vercel/Telegram Web App setup.
- Existing `positions` repo patterns:
  - Telegram Mini App typing/init: `/home/kcnc/code/positions/frontend/src/telegram.d.ts`
  - Mini App bootstrap: `/home/kcnc/code/positions/frontend/src/main.tsx`
  - `start_param` routing: `/home/kcnc/code/positions/frontend/src/app/routing/telegram-start-param.ts`
  - Telegram initData validation: `/home/kcnc/code/positions/internal/auth/telegram.go`
  - initData tests: `/home/kcnc/code/positions/internal/auth/telegram_test.go`
  - JWT/admin middleware shape: `/home/kcnc/code/positions/internal/auth/jwt.go`, `/home/kcnc/code/positions/internal/auth/middleware.go`
  - Login handler pattern: `/home/kcnc/code/positions/internal/web/handlers/user_auth.go`
  - Telegram Web App button support: `/home/kcnc/code/positions/internal/bot/telegram.go`
  - Nginx Telegram-compatible CSP/proxy config: `/home/kcnc/code/positions/docker/nginx/nginx.conf`, `/home/kcnc/code/positions/frontend/nginx.conf`
  - Mini App design notes: `/home/kcnc/code/positions/docs/superpowers/specs/2026-04-06-hh-vacancy-bot-design.md`

## Important correction from positions

For this Hermes dashboard, do **not** create normal multi-user login. This dashboard is owner/admin-only.

Use the positions pattern conceptually:

1. Telegram `initData` is the identity proof.
2. Validate raw `initData` server-side using bot token.
3. Enforce admin/owner allowlist immediately after validation.
4. Only then allow BFF routes to call Hermes VPS API.

No client-side trust in `initDataUnsafe` except for display hints/routing.

## Task 1 acceptance criteria

- A separate Next.js app exists at `apps/telegram-business-dashboard/`.
- It uses App Router, TypeScript, Tailwind, and shadcn/ui.
- It has a minimal Telegram Web App bootstrap:
  - loads `https://telegram.org/js/telegram-web-app.js`;
  - calls `ready()` and `expand()` when Telegram object exists;
  - handles missing Telegram context gracefully.
- It has server-only Telegram initData validation helper.
- It has owner/admin-only session route.
- It has `.env.example` with all required env names and no secrets.
- It builds on local/Vercel without Hermes API being implemented yet.
- It documents Vercel root directory and Telegram BotFather/menu setup.
- It records Caddy/Nginx requirements for later VPS API exposure.

## Recommended app path

```text
apps/telegram-business-dashboard/
```

Do not use a Git submodule. Vercel can deploy a subdirectory as project root.

## CLI setup

From repo root:

```bash
cd /home/kcnc/code/hermes/hermes-agent
mkdir -p apps

# Use the project's VitePlus-provided Node/npm/npx if running on VPS.
# Locally, plain npx is fine if it resolves to the managed toolchain.
npx create-next-app@latest apps/telegram-business-dashboard \
  --typescript \
  --eslint \
  --tailwind \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --use-npm \
  --yes

cd apps/telegram-business-dashboard

npx shadcn@latest init -d

npx shadcn@latest add \
  button \
  card \
  badge \
  alert \
  skeleton \
  separator \
  tabs

npm install @tma.js/init-data-node server-only zod lucide-react
```

Notes:

- Do not use Vite for this app.
- Do not add `vite.config.ts`.
- Do not add `@tailwindcss/vite`.
- VitePlus is only the managed Node/npm/npx provider on the VPS; the app runtime/build is Next.js on Vercel.

## Required files

### `package.json`

Ensure scripts include:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint",
    "typecheck": "tsc --noEmit"
  },
  "engines": {
    "node": ">=20.11.0"
  }
}
```

### `.env.example`

```bash
# Server-only. Never expose as NEXT_PUBLIC_*.
TELEGRAM_BOT_TOKEN=

# Comma-separated Telegram numeric user IDs allowed to open the dashboard.
# This is the admin gate for the MVP.
TELEGRAM_ADMIN_USER_IDS=

# Public browser-safe metadata.
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=
NEXT_PUBLIC_TELEGRAM_WEBAPP_URL=http://localhost:3000

# Later tasks: Vercel BFF -> Hermes VPS API. Server-only.
HERMES_DASHBOARD_API_BASE_URL=
HERMES_DASHBOARD_API_TOKEN=
```

### `next.config.ts`

Use server routes, so do not set `output: "export"`.

Recommended starter:

```ts
import type { NextConfig } from "next";

const csp = [
  "default-src 'self'",
  "script-src 'self' https://telegram.org 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: https://t.me https://*.t.me",
  "connect-src 'self'",
  "font-src 'self' data:",
  "frame-ancestors 'self' https://web.telegram.org https://web-k.telegram.org https://web-a.telegram.org"
].join("; ");

const nextConfig: NextConfig = {
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
          { key: "Content-Security-Policy", value: csp }
        ]
      }
    ];
  }
};

export default nextConfig;
```

Why this mirrors positions:

- positions allows Telegram scripts/widgets and Telegram Web frame ancestors.
- Keep `frame-ancestors` Telegram-compatible; do not set `X-Frame-Options: DENY`.

### `src/app/layout.tsx`

```tsx
import type { Metadata, Viewport } from "next";
import Script from "next/script";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hermes Business Dashboard",
  description: "Telegram Web App dashboard for Hermes Business chats."
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
  themeColor: "#020617"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
        {children}
      </body>
    </html>
  );
}
```

### `src/types/telegram-web-app.d.ts`

Based on positions `frontend/src/telegram.d.ts`, keep only the subset needed now:

```ts
export {};

declare global {
  interface TelegramWebAppUser {
    id: number;
    first_name: string;
    last_name?: string;
    username?: string;
    language_code?: string;
    photo_url?: string;
  }

  interface TelegramWebAppInitDataUnsafe {
    query_id?: string;
    user?: TelegramWebAppUser;
    auth_date?: number;
    hash?: string;
    start_param?: string;
  }

  interface TelegramBackButton {
    isVisible: boolean;
    show(): void;
    hide(): void;
    onClick(cb: () => void): void;
    offClick(cb: () => void): void;
  }

  interface TelegramHapticFeedback {
    impactOccurred(style: "light" | "medium" | "heavy" | "rigid" | "soft"): void;
    notificationOccurred(type: "error" | "success" | "warning"): void;
    selectionChanged(): void;
  }

  interface TelegramWebApp {
    initData: string;
    initDataUnsafe: TelegramWebAppInitDataUnsafe;
    version: string;
    platform: string;
    colorScheme: "light" | "dark";
    isExpanded: boolean;
    viewportHeight: number;
    viewportStableHeight: number;
    themeParams?: Record<string, string>;
    ready(): void;
    expand(): void;
    close(): void;
    BackButton: TelegramBackButton;
    HapticFeedback: TelegramHapticFeedback;
    onEvent(eventType: string, callback: () => void): void;
    offEvent(eventType: string, callback: () => void): void;
  }

  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}
```

### `src/lib/server/telegram-auth.ts`

Positions validates initData manually in Go. In Next, use `@tma.js/init-data-node`, but preserve the same semantics:

- parse raw query-string initData;
- validate HMAC using bot token;
- enforce max age;
- require user;
- then require admin allowlist.

```ts
import "server-only";

import { parse, validate } from "@tma.js/init-data-node";

const INIT_DATA_MAX_AGE_SECONDS = 5 * 60; // positions uses 5 minutes

export type TelegramAdminSession = {
  telegramUserId: number;
  username?: string;
  firstName?: string;
};

function adminIds(): Set<number> {
  return new Set(
    (process.env.TELEGRAM_ADMIN_USER_IDS ?? "")
      .split(",")
      .map((value) => Number(value.trim()))
      .filter((value) => Number.isSafeInteger(value) && value > 0)
  );
}

export function validateTelegramAdminInitData(initData: string): TelegramAdminSession {
  const botToken = process.env.TELEGRAM_BOT_TOKEN;
  if (!botToken) throw new Error("TELEGRAM_BOT_TOKEN is not configured");
  if (!initData) throw new Error("missing initData");

  validate(initData, botToken, { expiresIn: INIT_DATA_MAX_AGE_SECONDS });
  const parsed = parse(initData);
  const user = parsed.user;
  const id = Number(user?.id);
  if (!Number.isSafeInteger(id) || id <= 0) throw new Error("missing Telegram user");

  const allowed = adminIds();
  if (!allowed.has(id)) throw new Error("admin access required");

  return {
    telegramUserId: id,
    username: user?.username,
    firstName: user?.firstName
  };
}
```

### `src/app/api/session/route.ts`

```ts
import { NextRequest, NextResponse } from "next/server";
import { validateTelegramAdminInitData } from "@/lib/server/telegram-auth";

export const runtime = "nodejs";

type Body = { initData?: unknown };

export async function POST(request: NextRequest) {
  let body: Body;
  try {
    body = (await request.json()) as Body;
  } catch {
    return NextResponse.json({ ok: false, error: "invalid_json" }, { status: 400 });
  }

  if (typeof body.initData !== "string" || !body.initData) {
    return NextResponse.json({ ok: false, error: "missing_init_data" }, { status: 400 });
  }

  try {
    const session = validateTelegramAdminInitData(body.initData);
    return NextResponse.json({ ok: true, user: session });
  } catch (error) {
    const message = error instanceof Error ? error.message : "unauthorized";
    const status = message.includes("admin") ? 403 : 401;
    return NextResponse.json({ ok: false, error: status === 403 ? "forbidden" : "unauthorized" }, { status });
  }
}
```

### `src/lib/telegram/use-telegram-webapp.ts`

```ts
"use client";

import { useEffect, useState } from "react";

export type TelegramState =
  | { status: "loading" }
  | { status: "missing" }
  | { status: "ready"; initData: string; user?: TelegramWebAppUser };

export function useTelegramWebApp(): TelegramState {
  const [state, setState] = useState<TelegramState>({ status: "loading" });

  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    if (!webApp?.initData) {
      setState({ status: "missing" });
      return;
    }

    webApp.ready();
    webApp.expand();
    setState({ status: "ready", initData: webApp.initData, user: webApp.initDataUnsafe.user });
  }, []);

  return state;
}
```

### `src/app/page.tsx`

Minimal Task 1 page: validate Telegram admin session and show placeholder shell.

```tsx
"use client";

import { useEffect, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useTelegramWebApp } from "@/lib/telegram/use-telegram-webapp";

type SessionState =
  | { status: "idle" }
  | { status: "checking" }
  | { status: "admin" }
  | { status: "forbidden" }
  | { status: "error"; message: string };

export default function HomePage() {
  const telegram = useTelegramWebApp();
  const [session, setSession] = useState<SessionState>({ status: "idle" });

  useEffect(() => {
    if (telegram.status !== "ready") return;

    setSession({ status: "checking" });
    fetch("/api/session", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ initData: telegram.initData })
    })
      .then(async (response) => {
        if (response.status === 403) {
          setSession({ status: "forbidden" });
          return;
        }
        if (!response.ok) throw new Error("Telegram session validation failed");
        setSession({ status: "admin" });
      })
      .catch((error: Error) => setSession({ status: "error", message: error.message }));
  }, [telegram]);

  return (
    <main className="min-h-dvh bg-background p-4 text-foreground">
      <Card className="mx-auto max-w-xl">
        <CardHeader>
          <CardTitle>Hermes Business Dashboard</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {(telegram.status === "loading" || session.status === "checking") && (
            <>
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-24 w-full" />
            </>
          )}

          {telegram.status === "missing" && (
            <Alert>
              <AlertTitle>Open from Telegram</AlertTitle>
              <AlertDescription>This dashboard is available only as a Telegram Web App.</AlertDescription>
            </Alert>
          )}

          {session.status === "forbidden" && (
            <Alert variant="destructive">
              <AlertTitle>Admin only</AlertTitle>
              <AlertDescription>Your Telegram account is not allowed to access this dashboard.</AlertDescription>
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
              <AlertTitle>Admin session verified</AlertTitle>
              <AlertDescription>Business chat data will appear here in the next task.</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
```

## Vercel configuration

Project settings:

```text
Framework Preset: Next.js
Root Directory: apps/telegram-business-dashboard
Install Command: npm install
Build Command: npm run build
Output Directory: .next
Node.js Version: 20.x or 22.x
```

Env vars:

```bash
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ADMIN_USER_IDS=123456789
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_bot_username
NEXT_PUBLIC_TELEGRAM_WEBAPP_URL=https://your-vercel-project.vercel.app
```

Later, after VPS API exists:

```bash
HERMES_DASHBOARD_API_BASE_URL=https://your-vps-domain.example/api/business-dashboard
HERMES_DASHBOARD_API_TOKEN=...
```

Vercel CLI optional:

```bash
cd /home/kcnc/code/hermes/hermes-agent/apps/telegram-business-dashboard
npx vercel link
npx vercel env add TELEGRAM_BOT_TOKEN production
npx vercel env add TELEGRAM_ADMIN_USER_IDS production
npx vercel env add NEXT_PUBLIC_TELEGRAM_BOT_USERNAME production
npx vercel env add NEXT_PUBLIC_TELEGRAM_WEBAPP_URL production
npx vercel --prod
```

## Telegram configuration

### BotFather / Mini App

After Vercel URL exists:

1. Open `@BotFather`.
2. Use `/newapp` if creating a named Mini App.
3. Use `/setmenubutton` for the bot.
4. Button text: `Dashboard` or `Business`.
5. URL: Vercel production URL.

For named Mini App deep links later:

```text
https://t.me/<bot_username>/<mini_app_short_name>
https://t.me/<bot_username>/<mini_app_short_name>?startapp=business
```

### Hermes bot launcher

Task 1 can document only; Task 7 implements. The Hermes Telegram adapter should later mirror positions `SetChatMenuButton` / `WebAppInfo` pattern:

- send inline button with `web_app={url: TELEGRAM_BUSINESS_DASHBOARD_WEBAPP_URL}` from `/business`;
- optionally call Bot API `setChatMenuButton` at startup if configured;
- fallback to current inline `/business` panel if URL missing.

Config names:

```text
telegram.business_dashboard_webapp_url
TELEGRAM_BUSINESS_DASHBOARD_WEBAPP_URL
```

## VPS Caddy/Nginx notes for later Hermes API

Even though the Web App is hosted on Vercel, the Hermes dashboard API must be exposed over HTTPS for Vercel server route handlers.

### Nginx pattern from positions

Important details from positions:

- redirect HTTP to HTTPS;
- set TLS 1.2/1.3;
- pass proxy headers:
  - `Host`
  - `X-Real-IP`
  - `X-Forwarded-For`
  - `X-Forwarded-Proto`
- disable buffering/cache for API where responses may stream or need freshness;
- set `client_max_body_size` small/explicit;
- rate limit API/login routes;
- Telegram-compatible CSP for pages that load Telegram JS or run inside Telegram.

For Hermes API endpoint behind nginx:

```nginx
limit_req_zone $binary_remote_addr zone=business_dashboard_api:10m rate=10r/s;

server {
    listen 443 ssl;
    http2 on;
    server_name hermes-api.example.com;

    ssl_protocols TLSv1.2 TLSv1.3;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    client_max_body_size 1m;

    location /api/business-dashboard/ {
        limit_req zone=business_dashboard_api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8787/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 120s;
    }
}
```

### Caddy equivalent

If using Caddy instead of nginx:

```caddyfile
hermes-api.example.com {
    encode zstd gzip

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
        Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()"
        -Server
    }

    request_body {
        max_size 1MB
    }

    handle_path /api/business-dashboard/* {
        reverse_proxy 127.0.0.1:8787 {
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }
}
```

If Caddy rate limiting is required, it needs a rate-limit plugin/module; stock Caddy does not ship nginx-style `limit_req`.

### API CORS stance

Preferred: browser never calls VPS API directly.

```text
Browser -> Vercel Next route handler -> VPS API
```

Therefore:

- VPS API can omit CORS entirely.
- Require `Authorization: Bearer HERMES_DASHBOARD_API_TOKEN`.
- Also pass `X-Telegram-User-Id` from the verified Vercel session for audit.

## Admin-only authorization details

Positions has two relevant auth layers:

1. Telegram identity proof:
   - `ValidateInitData(initData, botToken)` validates Mini App HMAC with secret key `HMAC_SHA256("WebAppData", botToken)`;
   - validates `auth_date` freshness;
   - extracts `user.id`.
2. App authorization:
   - JWT claims include `role`;
   - `AdminMiddleware()` requires `role == "admin"`.

Hermes dashboard MVP should simplify this:

- no database user upsert required in Task 1;
- no JWT required in Task 1;
- server route validates Telegram initData and checks `TELEGRAM_ADMIN_USER_IDS`;
- every Next BFF route repeats validation or uses a short-lived httpOnly session cookie in a later task.

Task 1 should avoid persistent login state unless needed. Stateless validation is simpler and safer for one admin.

Later optimization:

- `/api/session` can set an httpOnly, SameSite=None/Secure session cookie for the Web App session;
- BFF routes validate that cookie instead of re-sending initData;
- still keep `initData` validation as the bootstrap root of trust.

## Local validation commands

```bash
cd /home/kcnc/code/hermes/hermes-agent/apps/telegram-business-dashboard
npm run lint
npm run typecheck
npm run build
npm run dev
```

Expected outside Telegram:

```text
Open from Telegram
```

Expected with invalid or non-admin initData fixture:

```text
Admin only / Authorization failed
```

## Pitfalls

- Never expose `TELEGRAM_BOT_TOKEN` or `HERMES_DASHBOARD_API_TOKEN` with `NEXT_PUBLIC_`.
- Never trust `initDataUnsafe` without validating raw `initData` server-side.
- Telegram `auth_date` should be short-lived; positions uses 5 minutes.
- Do not set `X-Frame-Options: DENY`; it can break Telegram Web App embedding.
- CSP must allow `https://telegram.org` script and Telegram web frame ancestors if served through custom proxy.
- Do not use static export; Next route handlers are needed.
- Set Vercel root directory correctly, or Vercel will try building the Hermes repo root.
- If VPS API is behind Cloudflare/Caddy/nginx, preserve `X-Forwarded-Proto` and do not log bearer tokens.
