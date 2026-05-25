# Hermes Telegram Business Dashboard

Telegram Web App dashboard for Hermes Business chats.

## Local setup

```bash
cp .env.example .env.local
npm install
npm run dev
```

Opening `http://localhost:3000` outside Telegram should show the safe `Open from Telegram` state.

## Auth tests

```bash
npm run test:auth
```

The auth tests generate signed Telegram Web App `initData` fixtures with `@tma.js/init-data-node` and do not require real bot credentials.

## Required Vercel env

```bash
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_USER_IDS=
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=
NEXT_PUBLIC_TELEGRAM_WEBAPP_URL=
```

Server-side Business dashboard BFF routes also require:

```bash
HERMES_DASHBOARD_API_BASE_URL=
HERMES_DASHBOARD_API_TOKEN=
```

Keep both Hermes values server-only. Do not create `NEXT_PUBLIC_` mirrors for the service token.

After deploying, set the same public Web App URL in the Hermes gateway on the
VPS as either config or env so `/business` sends the Telegram Web App button:

```yaml
telegram:
  business_dashboard_webapp_url: https://<your-vercel-app>.vercel.app
```

```bash
TELEGRAM_BUSINESS_DASHBOARD_WEBAPP_URL=https://<your-vercel-app>.vercel.app
```

## Vercel project settings

```text
Framework Preset: Next.js
Root Directory: apps/telegram-business-dashboard
Install Command: npm install
Build Command: npm run build
Output Directory: .next
Node.js Version: 20.x or 22.x
```

## Auth model

The app validates raw Telegram Web App `initData` server-side and then checks `TELEGRAM_ADMIN_USER_IDS`. Do not trust `initDataUnsafe` for authorization.
