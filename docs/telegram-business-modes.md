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
- `/business` opens the owner control panel listing known Business chats by
  mode, with inline mode-switch buttons. Raw chat IDs are not part of the main
  UX; callback data uses opaque tokens.
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
list/detail responses. Draft requests are safety-first: they enqueue through an
injected gateway callback when embedded, or mark the registry request state when
run as a separate service. The API never sends customer-facing Telegram text
itself.

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
