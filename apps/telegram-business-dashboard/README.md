# Hermes Telegram Business Dashboard

Telegram Web App dashboard for Hermes Business chats.

## Local setup

```bash
cp .env.example .env.local
npm install
npm run dev
```

Opening `http://localhost:3000` outside Telegram should show the safe `Open from Telegram` state.

## Required Vercel env

```bash
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_USER_IDS=
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=
NEXT_PUBLIC_TELEGRAM_WEBAPP_URL=
```

Later Hermes API tasks will use:

```bash
HERMES_DASHBOARD_API_BASE_URL=
HERMES_DASHBOARD_API_TOKEN=
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
