# Telegram Business per-chat modes

Hermes treats Telegram Business chats as opt-in per customer. Unknown Business
customer chats are gated before the agent runs, so they do not generate drafts
or send replies until the owner chooses a mode.

## Modes

- `Ignore` / `ignored`: silently ignore messages from this Business customer.
- `Watch` / `watch`: notify the owner with a safe inline card; do not run the
  agent, do not generate a draft, and do not send to the customer.
- `Draft` / `draft`: run the normal agent path. Replies are still routed to the
  owner approval card and are only sent after the owner clicks **Send**.
- `Auto` / `auto`: explicit opt-in direct Business replies. Hermes only sends
  when Telegram reports that the Business connection can reply.

Defaults:

- Human-looking unknown chats default to `watch` and get an owner mode card.
- Bot-looking chats default to `ignored`.
- Override defaults with `telegram.business_default_mode`,
  `telegram.business_bot_default_mode`, or env vars
  `TELEGRAM_BUSINESS_DEFAULT_MODE`, `TELEGRAM_BUSINESS_BOT_DEFAULT_MODE`.

## Owner UX

- New human Business chats send a card to the configured owner/home chat with
  buttons: **Ignore**, **Watch**, **Draft**, **Auto**.
- `/business` opens the Telegram Web App dashboard when
  `telegram.business_dashboard_webapp_url` (or
  `TELEGRAM_BUSINESS_DASHBOARD_WEBAPP_URL`) is configured. The bot sends an
  **Open dashboard** Telegram Web App button and does not log the configured
  URL.
- If no dashboard URL is configured, `/business` falls back to the owner
  control panel listing known Business chats by mode, with inline mode-switch
  buttons. Raw chat IDs are not part of the main UX; callback data uses opaque
  tokens.
- Mode callbacks require owner authorization.

## Watch mode and rules

Watch mode sends owner notifications with buttons for safe follow-up actions:

- **Draft once** arms the next customer message to go through the `draft` path.
- **Set Draft** changes the chat mode to `draft`.
- **Ignore** changes the chat mode to `ignored`.
- **Add rule** asks for the next owner message and stores it as a notify-only
  rule for this chat. Send any slash command instead to cancel.

The registry supports notify-only rules stored on each chat. Rule matching is
bounded and deterministic; a match only changes the owner notification text. It
never executes tools, never performs auto-actions, and never sends to the
customer.

## Storage and privacy

The registry is stored at:

`~/.hermes/gateway/platforms/telegram/business_chats.json`

The file and parent directory are written with private permissions. Entries are
keyed by Business connection + customer chat + optional direct-message topic;
display names are metadata only and are not used for routing. The registry keeps
short message previews for owner cards and watch notifications.

## Dashboard launcher config

Use config.yaml for the canonical non-secret Web App URL:

```yaml
telegram:
  business_dashboard_webapp_url: https://<your-vercel-app>.vercel.app
```

For VPS/systemd deployments you can set the equivalent environment variable;
it takes precedence in the gateway runtime config loader:

```text
TELEGRAM_BUSINESS_DASHBOARD_WEBAPP_URL=https://<your-vercel-app>.vercel.app
```

Unset both values to roll back `/business` to the inline owner panel.

## Dashboard VPS API runtime

The Telegram Business dashboard backend lives in
`gateway/platforms/telegram_business_dashboard_api.py`. It exposes a tiny JSON
API over the existing Business chat and approval stores:

- `GET /api/business/chats?mode=all|watch|draft|auto|ignored&q=...`
- `GET /api/business/chats/{token}`
- `GET /api/business/chats/{token}/history`
- `GET /api/business/approvals?chatToken=...`
- `POST /api/business/chats/{token}/mode` with `{ "mode": "watch" }`
- `POST /api/business/chats/{token}/draft` with `{ "source": "latest" }`

All dashboard API requests except `/health` require:

```http
Authorization: Bearer <HERMES_DASHBOARD_API_TOKEN>
X-Telegram-User-Id: <verified owner Telegram user id>
```

Set the service token as an environment variable, not in committed config:

```text
HERMES_DASHBOARD_API_TOKEN=replace-with-secret-service-token
HERMES_BUSINESS_DASHBOARD_API_HOST=127.0.0.1
HERMES_BUSINESS_DASHBOARD_API_PORT=8765
```

The API serializes view models for the dashboard and does not expose raw
Business connection IDs, customer chat IDs, or direct topic IDs in normal chat
list/detail responses. Mutating and read dashboard endpoints require both the
bearer token and `X-Telegram-User-Id`; missing or malformed actor headers are
rejected before any store mutation.

Draft requests are safety-first: they enqueue only through an injected gateway
callback when the API is embedded with the live Telegram gateway. A standalone
API process has no in-memory gateway queue, so `POST /draft` returns
`503 {"error":{"code":"not_connected",...}}` instead of claiming the request
was queued. Dashboard mode changes to `draft` or `auto` also try the same latest
message enqueue callback when embedded; when no callback is available the mode is
changed but `modeChange.status`/`lastDashboardModeEnqueueStatus` records
`no_enqueue_callback` so the dashboard never reports a false queued state. The
API never sends customer-facing Telegram text itself.

The module has a standalone entrypoint, so the API can run as a separate user
service:

```bash
python -m gateway.platforms.telegram_business_dashboard_api
```

Example user systemd unit for a standalone localhost service behind Caddy/nginx:

```ini
[Unit]
Description=Hermes Telegram Business Dashboard API
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/kcnc/code/hermes/hermes-agent
Environment=HERMES_DASHBOARD_API_TOKEN=replace-with-secret-service-token
Environment=HERMES_BUSINESS_DASHBOARD_API_HOST=127.0.0.1
Environment=HERMES_BUSINESS_DASHBOARD_API_PORT=8765
ExecStart=/home/kcnc/code/hermes/hermes-agent/venv/bin/python -m gateway.platforms.telegram_business_dashboard_api
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Expose it only over HTTPS from the VPS reverse proxy to the Vercel server-side
BFF, and keep browser CORS closed unless a later deployment explicitly needs an
allowlisted origin. Do not log or commit the bearer token.

Caddy example:

```caddyfile
business-api.example.com {
  reverse_proxy 127.0.0.1:8765
}
```

Nginx example:

```nginx
server {
  listen 443 ssl http2;
  server_name business-api.example.com;

  location / {
    proxy_pass http://127.0.0.1:8765;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto https;
  }
}
```

## Vercel dashboard app env

Set the Vercel project root to `apps/telegram-business-dashboard` and configure
these environment variable names in Vercel:

```text
TELEGRAM_BOT_TOKEN              # server-only; validates Telegram initData
TELEGRAM_ADMIN_USER_IDS         # comma-separated owner Telegram user IDs
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME
NEXT_PUBLIC_TELEGRAM_WEBAPP_URL # public Vercel app URL shown in fallback UI
HERMES_DASHBOARD_API_BASE_URL   # HTTPS URL for the VPS API reverse proxy
HERMES_DASHBOARD_API_TOKEN      # server-only; matches the VPS API token
```

After Vercel deploys, copy the public app URL into the Hermes gateway setting
`telegram.business_dashboard_webapp_url` or the VPS env var
`TELEGRAM_BUSINESS_DASHBOARD_WEBAPP_URL` so `/business` launches the Web App.
