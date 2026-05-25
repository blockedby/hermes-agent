# Plan: Telegram Business Telegram Web App dashboard

Date: 2026-05-25
Repo: `/home/kcnc/code/hermes/hermes-agent`
Status: revised after owner clarified: **not an inline bot dashboard; build a Telegram Web App page hosted on Vercel with Next.js + shadcn/ui**.

## Goal

Build a modern Telegram Web App dashboard for Telegram Business chats.

The owner opens it from the Telegram bot. The page is hosted on Vercel, implemented as a small Next.js app with shadcn/ui/Tailwind, and talks to a minimal authenticated Hermes Business Dashboard API on the VPS.

Owner capabilities:

- list known Business chats;
- see chat mode/status/reply capability/pending drafts;
- inspect bounded message/action history;
- request draft generation on demand;
- change mode/status: `ignored`, `watch`, `draft`, `auto`;
- open/approve/cancel generated drafts through the existing safe approval flow or a dashboard-backed equivalent;
- keep code intentionally minimal and maintainable.

## Revised direction

Previous plan targeted Telegram inline bot messages and callback pagination. That is now deprecated for this feature. Keep current `/business` inline panel as a fallback/control entrypoint, but the primary UX should be:

1. Telegram owner sends `/business` or taps menu.
2. Bot sends/opens a **Telegram Web App** button.
3. Web App loads from Vercel.
4. Next.js verifies Telegram `initData` server-side.
5. Next.js calls a small Hermes VPS API using a server-only service token.
6. Hermes API reads/writes the existing Business chat stores and queues draft generation through existing gateway logic.

## Current repo orientation

Relevant existing backend code:

- `gateway/platforms/telegram.py`
  - `_send_business_control_panel()` currently implements `/business` as a basic inline list.
  - `_business_mode_keyboard()` and `bm:*` callbacks already support mode changes.
  - `_business_event_from_chat_entry()` reconstructs a `MessageEvent` from latest Business message.
  - `_maybe_enqueue_business_mode_event()` enqueues latest message for `draft`/`auto` mode changes.
  - `ba:*` callbacks implement safe owner approval for generated drafts.
- `gateway/platforms/telegram_business_chats.py`
  - persistent registry in `business_chats.json`.
  - stores mode, token, display name, direct topic id, last message text/preview/id, rules.
- `gateway/platforms/telegram_business_approvals.py`
  - stores pending/resolved draft approval state in `business_approvals.json`.
- `docs/telegram-business-modes.md`
  - documents current bot-only owner UX and modes.
- Tests:
  - `tests/gateway/test_telegram_business.py` covers registry, callbacks, approvals, mode changes, and Business direct-topic regression.

Relevant existing frontend code:

- `web/` is a Vite React app with Tailwind-related dependencies, but the owner requested **Next.js + shadcn + Vercel** for this dashboard.
- Recommended: create a separate small app instead of mutating the existing Vite app.

## Proposed architecture

```text
Telegram mobile/desktop
  └─ Telegram Web App initData
      └─ Vercel Next.js app: apps/telegram-business-dashboard
          ├─ UI: shadcn/ui + Tailwind + lucide-react
          ├─ Route handlers: /api/business/*
          ├─ validate Telegram initData with TELEGRAM_BOT_TOKEN
          ├─ owner allowlist check
          └─ server-to-server calls with HERMES_DASHBOARD_API_TOKEN
              └─ Hermes VPS Dashboard API
                  ├─ reads business_chats.json
                  ├─ reads business_approvals.json
                  ├─ reads/writes business_history.json
                  ├─ changes modes through registry
                  └─ enqueues draft generation through existing gateway path
```

### App location

Recommended new app path:

```text
apps/telegram-business-dashboard/
```

Reason:

- Keeps Next.js/Vercel app isolated from existing `web/` Vite app.
- Makes Vercel project root simple.
- Keeps dashboard dependency surface small.

Alternative if repo policy prefers no `apps/`: `web-telegram-business/`. Pick one and keep it boring.

### Minimal Next.js stack

- Next.js App Router.
- TypeScript.
- Tailwind CSS.
- shadcn/ui copied components only as needed:
  - `button`
  - `card`
  - `badge`
  - `tabs`
  - `sheet` or `drawer` only if detail view benefits from it
  - `skeleton`
  - `toast`/`sonner` optional
- No Redux/Zustand unless proven necessary.
- Prefer simple server route handlers + small client components.
- Use Telegram theme params via CSS variables when available.
- Use compact mobile-first layout; Telegram Web Apps are primarily mobile surfaces.

## Security model

### Telegram Web App auth

Client receives `window.Telegram.WebApp.initData`.

Server verifies initData on every API session/bootstrap request using `TELEGRAM_BOT_TOKEN` in Vercel env:

- parse initData;
- verify Telegram HMAC;
- enforce freshness window, e.g. `auth_date` not older than 24h;
- extract Telegram user id;
- check owner allowlist.

Vercel env vars:

```text
TELEGRAM_BOT_TOKEN              # server-only; used to validate initData
TELEGRAM_ADMIN_USER_IDS         # comma-separated owner Telegram user IDs
HERMES_DASHBOARD_API_BASE_URL   # HTTPS URL to VPS dashboard API
HERMES_DASHBOARD_API_TOKEN      # server-only service token for Vercel -> VPS
```

Do not expose tokens to client bundles. Client only sends Telegram initData to Next route handlers.

### VPS API auth

Hermes dashboard API requires:

```http
Authorization: Bearer <HERMES_DASHBOARD_API_TOKEN>
X-Telegram-User-Id: <verified owner user id>
```

The VPS API should not be usable directly from browsers. CORS can be disabled or only allow Vercel origin; bearer token is still mandatory.

### Customer safety

- Changing mode to `auto` remains owner-only and visually marked as risky.
- `Generate draft now` must not directly send to customer.
- Generated drafts go through existing Business draft approval state unless the user later explicitly designs a separate dashboard approval send flow.
- Any direct dashboard send feature is out of MVP unless it reuses the same approval guardrails and audit state.

## Data/API design

### Hermes VPS Dashboard API

Add a tiny API surface near the gateway, either:

- inside the existing gateway process if there is an established HTTP/admin server pattern; or
- as a small separate user service, e.g. `hermes-business-dashboard-api.service`, sharing the same store files and queue mechanism.

Prefer the implementation that minimizes new runtime complexity. If embedded HTTP would make gateway lifecycle risky, use a separate small service.

Proposed endpoints:

```http
GET  /api/business/summary
GET  /api/business/chats?mode=all|watch|draft|auto|ignored&q=&cursor=
GET  /api/business/chats/{token}
POST /api/business/chats/{token}/mode        { "mode": "watch" }
POST /api/business/chats/{token}/draft       { "source": "latest" }
GET  /api/business/chats/{token}/history?cursor=
GET  /api/business/approvals?chatToken=...
```

MVP can collapse `summary` into `chats` if simpler.

Response shape should be view-model oriented and avoid exposing raw internal IDs unless required:

```json
{
  "token": "opaque-token",
  "displayName": "Customer",
  "username": "customer",
  "mode": "watch",
  "lastSeenAt": 0,
  "lastMessagePreview": "...",
  "canReply": "yes|no|unknown",
  "pendingDraftCount": 0,
  "failedDraftCount": 0,
  "rulesCount": 0,
  "hasDirectTopic": true
}
```

### Bounded history store

Add `gateway/platforms/telegram_business_history.py`:

```text
~/.hermes/gateway/platforms/telegram/business_history.json
```

Shape:

```json
{
  "version": 1,
  "updated_at": 0,
  "events": {
    "<business-chat-key>": [
      {
        "event_id": "...",
        "created_at": 0,
        "type": "inbound|draft_requested|draft_generated|approval_sent|approval_cancelled|approval_failed|outbound_sent|mode_changed|rule_matched",
        "preview": "bounded text",
        "message_id": "...",
        "approval_id": "...",
        "mode": "watch",
        "actor_user_id": "..."
      }
    ]
  }
}
```

Limits:

- max events per chat: 50 for MVP;
- max preview chars: 500;
- private file perms like existing stores;
- atomic writes like `TelegramBusinessChatRegistry`.

## Telegram bot integration

### `/business`

Keep `/business`, but change primary response to a Web App launcher:

- compact text: `Open Telegram Business Dashboard`;
- inline keyboard button with `web_app=WebAppInfo(url=<dashboard url>)`;
- optional fallback buttons: current inline panel, mode card help, refresh.

Config/env:

```text
telegram.business_dashboard_webapp_url
TELEGRAM_BUSINESS_DASHBOARD_WEBAPP_URL
```

If URL is missing, keep the current inline `/business` panel.

### Bot menu button

Optional MVP+:

- set Telegram chat/menu button to launch the dashboard for owner chats.
- This can be a documented manual command/script first; no need to overbuild.

## UI requirements

### Main dashboard

Mobile-first screen:

- header: `Business` + refresh status;
- count cards/chips:
  - all;
  - watch;
  - draft;
  - auto;
  - ignored;
  - pending drafts;
- search input/filter tabs;
- chat list cards:
  - customer name + username;
  - mode badge;
  - last seen relative time;
  - last message preview;
  - pending/failed draft indicator.

States:

- loading skeleton;
- empty state;
- error with retry;
- unauthorized state;
- stale/offline state.

### Chat detail

Can be a route or drawer:

```text
/chats/[token]
```

Shows:

- customer display name/username;
- current mode;
- reply capability: can reply / disabled / unknown;
- pending/failed drafts;
- latest message preview;
- recent history timeline;
- rules count.

Actions:

- `Generate draft now`;
- mode segmented control: Ignore / Watch / Draft / Auto;
- history refresh;
- optional `Back to list`.

### Visual style

- shadcn defaults, minimal custom CSS.
- Use Telegram theme params to map background/text/button colors where possible.
- Avoid heavy animations.
- Keep one-column mobile layout; desktop can center max-width content.

## Task breakdown

### Task 1: Next.js/Vercel app skeleton + Telegram admin auth foundation

Expanded instruction:
- Detailed setup playbook: `reports/task-1-next-shadcn-telegram-setup.md`.
- GitHub sub-issue: https://github.com/blockedby/hermes-agent/issues/21

Goal:
- Create a minimal deployable Next.js Telegram Web App shell with shadcn/ui and admin-only Telegram `initData` validation.

Boundary:
- System area: frontend app setup, Telegram Web App bootstrap, server-side auth foundation, and deployment config.
- Primary verification: `npm run lint`, `npm run typecheck`, `npm run build`, Vercel-compatible build output.

Existing pattern / reuse:
- Existing repo Node baseline is Node >=20.
- Keep separate from `web/` Vite app.
- Reuse `positions` repo patterns conceptually:
  - Telegram Web App typing/bootstrap from `frontend/src/telegram.d.ts` and `frontend/src/main.tsx`.
  - Server-side Mini App HMAC validation from `internal/auth/telegram.go`.
  - Admin-only role gate concept from `internal/auth/middleware.go`.
  - Web App button/menu concept from `internal/bot/telegram.go`.
  - Telegram-compatible CSP/proxy headers from `docker/nginx/nginx.conf` and `frontend/nginx.conf`.

Missing change:
- Add `apps/telegram-business-dashboard` with Next.js App Router, TypeScript, Tailwind, shadcn setup.
- Add minimal Telegram Web App client wrapper that calls `ready()`/`expand()`.
- Add server-only Telegram initData validation helper.
- Add admin allowlist check using `TELEGRAM_ADMIN_USER_IDS`.
- Add `/api/session` route that validates raw initData and rejects non-admin users.
- Add Vercel project docs/env template.
- Add Caddy/Nginx notes for later HTTPS VPS API exposure.

Scope / likely files:
- `apps/telegram-business-dashboard/package.json`
- `apps/telegram-business-dashboard/next.config.ts`
- `apps/telegram-business-dashboard/src/app/layout.tsx`
- `apps/telegram-business-dashboard/src/app/page.tsx`
- `apps/telegram-business-dashboard/src/app/api/session/route.ts`
- `apps/telegram-business-dashboard/src/components/ui/*`
- `apps/telegram-business-dashboard/src/lib/server/telegram-auth.ts`
- `apps/telegram-business-dashboard/src/lib/telegram/use-telegram-webapp.ts`
- `apps/telegram-business-dashboard/src/types/telegram-web-app.d.ts`
- `apps/telegram-business-dashboard/.env.example`
- `docs/telegram-business-modes.md`
- `docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/task-1-next-shadcn-telegram-setup.md`

Acceptance criteria:
- App renders inside normal browser without crashing.
- Missing Telegram context shows `Open from Telegram`.
- Telegram Web App object is detected when present and `ready()`/`expand()` are called.
- `/api/session` validates raw Telegram initData server-side.
- `/api/session` rejects invalid signature/expired data.
- `/api/session` rejects valid but non-admin Telegram users.
- Build succeeds with no real secrets required.
- Vercel root directory and env vars are documented.
- Caddy/Nginx requirements for later VPS API are documented.

Test plan:
- Positive:
  - `npm run lint`, `npm run typecheck`, `npm run build` pass.
  - page renders dashboard shell outside Telegram as safe missing-context state.
  - valid admin initData fixture returns `{ ok: true }` from `/api/session`.
- Negative:
  - invalid hash returns 401.
  - expired `auth_date` returns 401.
  - valid non-admin user returns 403.
  - no `TELEGRAM_BOT_TOKEN` fails closed.
- Edge cases:
  - dark/light Telegram theme params.
  - long Telegram names/usernames.
  - local browser has no real Telegram initData.

Dependencies:
- Depends on: none.
- Blocks: Task 4 UI integration.
- Can run parallel with: Tasks 2 and 3.

Executor:
- aad-implementer with frontend-ui-quality and devops-runtime-readiness checklists.

### Task 2: Telegram Web App auth in Next route handlers

Goal:
- Verify Telegram initData server-side and enforce owner-only access.

Boundary:
- System area: frontend backend-for-frontend auth.
- Primary verification: unit tests for initData verification and owner allowlist.

Existing pattern / reuse:
- Telegram Web App initData HMAC spec.
- Existing Telegram owner ids/config concept in gateway.

Missing change:
- Add `lib/server/telegram-auth.ts`.
- Add `/api/session` or `/api/business/bootstrap` route.
- Validate `auth_date` freshness.
- Enforce `TELEGRAM_ADMIN_USER_IDS`.

Scope / likely files:
- `apps/telegram-business-dashboard/lib/server/telegram-auth.ts`
- `apps/telegram-business-dashboard/app/api/session/route.ts`
- tests if test runner is added, or focused Node test script.

Acceptance criteria:
- Valid owner initData returns session/bootstrap success.
- Valid non-owner initData returns 403.
- Invalid signature returns 401.
- Expired auth_date returns 401.
- Bot token is never sent to client.

Test plan:
- Positive:
  - generated valid initData fixture verifies.
- Negative:
  - bad hash;
  - missing user;
  - expired auth date;
  - owner not allowlisted.

Dependencies:
- Depends on: Task 1.
- Blocks: Task 4.
- Can run parallel with: Task 3.

Executor:
- aad-implementer with security notes.

### Task 3: Hermes VPS Business Dashboard API

Goal:
- Expose a tiny authenticated API over Business chats, approvals, history, and draft requests.

Boundary:
- System area: backend/API + runtime service.
- Primary verification: Python tests for auth, list/detail/mode/draft/history endpoints or handler functions.

Existing pattern / reuse:
- `TelegramBusinessChatRegistry`.
- `TelegramBusinessApprovalStore`.
- existing gateway queue helpers for Business events.

Missing change:
- Add a minimal API module/service.
- Add bearer-token auth.
- Add view-model serialization that hides unnecessary internal IDs.
- Add mode change and draft request operations.

Scope / likely files:
- `gateway/platforms/telegram_business_dashboard_api.py` or similar.
- `gateway/platforms/telegram.py` if embedded into adapter/gateway.
- config loader/env docs.
- tests under `tests/gateway/`.

Acceptance criteria:
- Unauthorized/missing bearer token returns 401/403.
- `GET chats` returns sorted/filterable view models.
- `GET chat detail` joins registry + approval + history summary.
- `POST mode` changes mode and records actor metadata.
- `POST draft` enqueues draft generation and never sends customer text directly.
- API can run on VPS with documented systemd/env wiring.

Test plan:
- Positive:
  - list/detail/mode/draft happy paths.
- Negative:
  - bad token;
  - invalid mode;
  - unknown chat token;
  - missing latest message for draft.
- Edge cases:
  - direct topic present;
  - long names/previews escaped/truncated;
  - corrupted store safe behavior.

Dependencies:
- Depends on: none.
- Blocks: Tasks 4 and 7.
- Can run parallel with: Tasks 1 and 2.

Executor:
- aad-implementer with backend-api-data-quality and devops-runtime-readiness checklists.

### Task 4: Next API proxy/BFF to Hermes VPS API

Goal:
- Make Vercel route handlers securely proxy dashboard operations to Hermes VPS.

Boundary:
- System area: Next route handlers / server-to-server integration.
- Primary verification: route-handler tests or mocked fetch checks; build success.

Existing pattern / reuse:
- Auth helper from Task 2.
- Hermes API from Task 3.

Missing change:
- Add route handlers:
  - `GET /api/business/chats`
  - `GET /api/business/chats/[token]`
  - `POST /api/business/chats/[token]/mode`
  - `POST /api/business/chats/[token]/draft`
  - `GET /api/business/chats/[token]/history`
- Ensure all require verified Telegram owner session.
- Add small typed fetch client.

Scope / likely files:
- `apps/telegram-business-dashboard/app/api/business/**/route.ts`
- `apps/telegram-business-dashboard/lib/server/hermes-api.ts`
- `apps/telegram-business-dashboard/lib/types.ts`

Acceptance criteria:
- Client never receives Hermes service token.
- Non-owner cannot proxy calls.
- Hermes API errors are mapped to useful UI-safe status/errors.
- Build works on Vercel.

Test plan:
- Positive:
  - mocked Hermes API returns chats/detail/history.
  - mode/draft POSTs include actor user id.
- Negative:
  - invalid Telegram session rejected before Hermes call.
  - Hermes 401/500 mapped safely.

Dependencies:
- Depends on: Tasks 2 and 3.
- Blocks: Task 5.
- Can run parallel with: Task 6 history store after API shape is known.

Executor:
- aad-implementer.

### Task 5: Dashboard UI list/detail/actions

Goal:
- Implement the modern dashboard interface.

Boundary:
- System area: browser-visible UI.
- Primary verification: component/UI tests if available, build/lint, manual browser evidence.

Existing pattern / reuse:
- shadcn/ui components.
- `lucide-react` icons.
- Telegram theme params.

Missing change:
- Main page list with filters/search/loading/error/empty states.
- Detail route/drawer with mode controls and `Generate draft now`.
- Client fetch hooks kept simple; no global state library unless needed.

Scope / likely files:
- `apps/telegram-business-dashboard/app/page.tsx`
- `apps/telegram-business-dashboard/app/chats/[token]/page.tsx` or client drawer components.
- `apps/telegram-business-dashboard/components/business/*`
- `apps/telegram-business-dashboard/components/ui/*`

Acceptance criteria:
- Owner can see chat list and mode counts.
- Owner can open chat detail.
- Owner can change mode with visible confirmation.
- Owner can request draft generation with visible queued state.
- UI handles loading/empty/error/unauthorized states.
- Mobile viewport has no horizontal overflow.

Test plan:
- Positive:
  - mocked data list renders.
  - detail renders all status sections.
  - mode/draft buttons call API routes and update UI.
- Negative:
  - API error shows retryable error message.
  - unauthorized shows locked state.
- Edge cases:
  - long names/messages;
  - empty history;
  - dark theme.
- Manual:
  - browser screenshot/check inside Telegram-like mobile viewport.

Dependencies:
- Depends on: Task 4.
- Blocks: final acceptance.
- Can run parallel with: Task 6 after API contracts stable.

Executor:
- aad-implementer with frontend-ui-quality and visual-composition-quality checklists.

### Task 6: Bounded Business history store and instrumentation

Goal:
- Provide recent message/action history for the dashboard.

Boundary:
- System area: backend storage + lifecycle instrumentation.
- Primary verification: focused Python tests for append/load/prune and rendered API response.

Existing pattern / reuse:
- `TelegramBusinessChatRegistry` JSON store style.
- `TelegramBusinessApprovalStore` validation style.

Missing change:
- Add `TelegramBusinessHistoryStore`.
- Append events at key lifecycle points:
  - inbound Business message recorded;
  - mode changed;
  - draft requested;
  - draft approval created;
  - draft sent/cancelled/failed/partial;
  - watch rule matched.

Scope / likely files:
- `gateway/platforms/telegram_business_history.py`
- `gateway/platforms/telegram.py`
- dashboard API serializer/tests.

Acceptance criteria:
- History is bounded per chat and private on disk.
- History API returns newest/relevant events with pagination/cursor.
- Long previews are truncated.
- Corrupt history file does not break dashboard.

Test plan:
- Positive:
  - append/load round trip;
  - prune oldest over limit;
  - lifecycle events append from Telegram adapter paths.
- Negative:
  - corrupt file safe fallback;
  - invalid event ignored/normalized.
- Edge cases:
  - HTML/control chars in preview;
  - many events.

Dependencies:
- Depends on: Task 3 API shape for history response.
- Blocks: final acceptance for history feature.
- Can run parallel with: Task 5 UI if mock history data is used.

Executor:
- aad-implementer.

### Task 7: Bot launcher + VPS/Vercel deployment wiring

Goal:
- Wire Telegram bot, Vercel app, and VPS API together safely.

Boundary:
- System area: runtime config/deployment.
- Primary verification: local build, VPS service status, Vercel deployment, Telegram launch smoke.

Existing pattern / reuse:
- `hermes-gateway.service` user service on VPS.
- `/business` current bot command.
- VitePlus-only Node/Codex preference on VPS does not apply to Vercel build, but VPS API must stay lightweight.

Missing change:
- Add config/env docs:
  - `TELEGRAM_BUSINESS_DASHBOARD_WEBAPP_URL`
  - `HERMES_DASHBOARD_API_TOKEN`
  - dashboard API bind/port/base URL.
- Update `/business` to send Web App button when URL configured.
- Add/adjust systemd user service if API is separate.
- Add Vercel env docs.

Scope / likely files:
- `gateway/platforms/telegram.py`
- config docs/examples.
- `docs/telegram-business-modes.md`
- Vercel project files in app dir.
- optional systemd/service docs/scripts.

Acceptance criteria:
- `/business` shows `Open dashboard` Web App button when configured.
- Missing dashboard URL falls back to old inline panel.
- Vercel app has required env documented.
- VPS API starts/restarts cleanly and logs no secrets.
- Telegram Web App can load from the bot and fetch real chat data.

Test plan:
- Automated:
  - callback/command test for URL configured vs missing fallback.
  - config validation tests if config loader supports it.
- Manual:
  - deploy Vercel preview/prod;
  - configure bot URL;
  - open `/business` in Telegram;
  - tap Web App;
  - verify list/detail/mode/draft actions.

Dependencies:
- Depends on: Tasks 1-5, Task 3 for API runtime.
- Blocks: release.
- Can run parallel with: docs updates after env names settle.

Executor:
- owner/aad-implementer with devops-runtime-readiness.

### Task 8: Final docs and acceptance verification

Goal:
- Make the feature maintainable and ready for VPS + Vercel production use.

Boundary:
- System area: docs, tests, smoke evidence.
- Primary verification: focused backend tests, frontend build/lint, gateway restart, Vercel smoke.

Scope / likely files:
- `docs/telegram-business-modes.md`
- task package `verification/*.md`
- maybe `apps/telegram-business-dashboard/README.md`

Acceptance criteria:
- Backend focused tests pass.
- Frontend lint/build pass.
- Gateway starts on VPS.
- Vercel deployment succeeds.
- Telegram Web App opens for owner and denies non-owner.
- Owner can list chats, open detail/history, request draft, and change mode.
- No customer direct sends occur from `Generate draft now`.

Verification commands:

Backend via Podman:

```bash
cd /home/kcnc/code/hermes/hermes-agent
podman run --rm -v "$PWD:/workspace:Z" -w /workspace localhost/hermes-agent:test-candidate-20260510T2030Z \
  bash -lc 'export PATH=/opt/hermes-test-venv/bin:$PATH HERMES_TEST_VENV=/opt/hermes-test-venv; python -m pytest -o addopts="" tests/gateway/test_telegram_business.py tests/gateway/test_telegram_thread_fallback.py -q --tb=short'
```

Frontend:

```bash
cd /home/kcnc/code/hermes/hermes-agent/apps/telegram-business-dashboard
npm run lint
npm run build
```

VPS smoke:

```bash
ssh everyday-white 'systemctl --user status hermes-gateway.service --no-pager'
ssh everyday-white 'journalctl --user -u hermes-gateway.service --since "10 minutes ago" --no-pager | tail -120'
```

Vercel smoke:

- deployment URL opens;
- outside Telegram shows `Open from Telegram`;
- Telegram owner Web App loads dashboard;
- non-owner initData fixture/API request denied.

## Dependency graph

```text
Task 1 Next app skeleton
  -> Task 2 Telegram initData auth
      -> Task 4 Next API proxy/BFF
          -> Task 5 Dashboard UI

Task 3 Hermes VPS API
  -> Task 4 Next API proxy/BFF
  -> Task 6 History store/instrumentation

Task 1 + Task 3 + Task 5
  -> Task 7 Bot launcher + deployment wiring

Tasks 1-7
  -> Task 8 Final docs/verification
```

## TDD order

1. Backend: tests for VPS API auth/list/detail/mode/draft behavior.
2. Backend: implement API/view models minimally.
3. Backend: tests for history store append/load/prune.
4. Backend: implement history store/instrumentation.
5. Frontend: tests or small fixtures for Telegram initData validation.
6. Frontend: implement Next auth route.
7. Frontend: implement BFF proxy route handlers with mocked Hermes API.
8. Frontend: build UI against mocked API data.
9. Integration: point Vercel preview at VPS API staging/prod token.
10. Bot: add Web App launcher and fallback tests.
11. Final smoke in Telegram.

## Open decisions

1. App path:
   - Recommendation: `apps/telegram-business-dashboard/`.
2. VPS API form:
   - Embedded in gateway vs separate user service.
   - Recommendation: choose after checking existing HTTP server patterns; prefer separate only if embedding is messy.
3. Public VPS URL:
   - Need HTTPS endpoint reachable from Vercel.
   - Options: Caddy/nginx on VPS, Cloudflare Tunnel, Tailscale Funnel, or existing domain/proxy.
4. Vercel project ownership:
   - Need project + env setup under owner account/org.
5. Dashboard approval send:
   - MVP should request drafts and rely on existing Telegram approval card.
   - Later: implement approval review/send inside Web App if needed.
6. History retention:
   - Recommendation: 50 events/chat for MVP.

## Out of scope for MVP

- Replacing all bot approval cards with Web App approval UI.
- Full media archive.
- Full transcript search.
- Multi-owner RBAC beyond existing owner allowlist.
- Analytics charts.
- Heavy client state management.
- Editing drafts in the dashboard before send, unless added as a follow-up.

## Rollout plan

1. Build and test backend API locally/Podman.
2. Build Next app locally.
3. Deploy VPS API and set service token.
4. Deploy Vercel preview with env vars.
5. Configure Telegram `/business` Web App URL to preview.
6. Smoke as owner.
7. Deploy Vercel production URL.
8. Update VPS config to production URL.
9. Monitor gateway/API logs.
10. Keep old inline `/business` fallback for rollback.

## Rollback plan

- Unset `TELEGRAM_BUSINESS_DASHBOARD_WEBAPP_URL` to restore old inline `/business` panel.
- Stop/disable separate dashboard API service if used.
- Vercel app can remain deployed but inaccessible without bot launcher and valid owner initData.
