# Final verification — Telegram Business Dashboard

Date: 2026-05-25
Branch/worktree: `epic/telegram-business-dashboard` at `/home/kcnc/code/hermes/hermes-agent`
Scope: Task 8 final docs and acceptance verification; no deploy, no push.

## Fresh command evidence

### Backend focused tests — PASS

Command:

```bash
HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh \
  tests/gateway/test_telegram_business_dashboard_api.py \
  tests/gateway/test_telegram_business.py \
  tests/gateway/test_config.py \
  -- -q --tb=short
```

Result summary:

```text
✓ tests/gateway/test_telegram_business_dashboard_api.py (15 passed)
✓ tests/gateway/test_telegram_business.py (68 passed)
✓ tests/gateway/test_config.py (50 passed)
=== Summary: 3 files, 133 tests passed, 0 failed in 1.7s ===
```

Coverage notes:
- Dashboard API/history: `tests/gateway/test_telegram_business_dashboard_api.py` covers bearer + actor auth, sorted/filterable chats, detail + approval/history joins, bounded private history store, pagination, mode changes, draft request safety, and corrupt-store fallback.
- Telegram Business behavior: `tests/gateway/test_telegram_business.py` covers Business registry/callbacks/approvals/mode behavior, dashboard launcher fallback/configured button, and history instrumentation.
- Config/runtime bridge: `tests/gateway/test_config.py` covers `telegram.business_dashboard_webapp_url` config/env bridging.

Setup notes:
- `scripts/run_tests.sh ... -q --tb=short` without `--` was rejected by the wrapper argument parser.
- `scripts/run_tests.sh ... -- -q --tb=short` without `HERMES_TEST_VENV` selected `.venv`, which lacks pytest in this checkout.
- The passing backend evidence used the repo wrapper with `HERMES_TEST_VENV=$PWD/venv`.

### Frontend auth/unit tests — PASS

Command:

```bash
cd apps/telegram-business-dashboard && npm run test:auth
```

Result summary:

```text
Test Files  5 passed (5)
Tests       30 passed (30)
Duration    305ms
```

Coverage notes:
- Telegram initData owner/non-owner/invalid/expired/missing-token auth.
- `/api/session` fail-closed behavior.
- Business BFF route auth gating, actor propagation, safe upstream error mapping, and service-token non-exposure.
- Dashboard UI/list/detail state and client BFF helper coverage.

### Frontend lint — PASS

Command:

```bash
cd apps/telegram-business-dashboard && npm run lint
```

Result summary: `eslint` completed with exit code 0 and no reported findings.

### Frontend typecheck — PASS

Command:

```bash
cd apps/telegram-business-dashboard && npm run typecheck
```

Result summary: `tsc --noEmit` completed with exit code 0.

### Frontend production build — PASS

Command:

```bash
cd apps/telegram-business-dashboard && npm run build
```

Result summary:

```text
▲ Next.js 16.2.6 (Turbopack)
✓ Compiled successfully in 2.3s
Finished TypeScript in 1982ms
✓ Generating static pages using 12 workers (5/5)
```

Route table includes:

```text
○ /
ƒ /api/business/chats
ƒ /api/business/chats/[token]
ƒ /api/business/chats/[token]/draft
ƒ /api/business/chats/[token]/history
ƒ /api/business/chats/[token]/mode
ƒ /api/session
ƒ /chats/[token]
```

## Artifact presence checks

- Browser smoke report present: `docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/browser-smoke.md`.
- Browser verification index present: `docs/plans/2026-05-25-telegram-business-bot-dashboard/verification/browser.md`.
- Browser smoke raw artifact present and tracked: `docs/plans/2026-05-25-telegram-business-bot-dashboard/artifacts/screenshots/browser-smoke/2026-05-25T191123Z/smoke-results.json`.
- Browser smoke screenshots present and tracked:
  - `artifacts/screenshots/browser-smoke/2026-05-25T191123Z/390x844-mobile-unauthorized.png`
  - `artifacts/screenshots/browser-smoke/2026-05-25T191123Z/1280x800-desktop-unauthorized.png`
- Reviewer-fixes report present and tracked: `docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/reviewer-fixes.md`.

Existing browser smoke result: PASS for outside-Telegram unauthorized rendering at `http://127.0.0.1:3107/`, with no horizontal overflow, no console/network blockers, and expected `Open from Telegram` state on 390x844 mobile and 1280x800 desktop.

## Acceptance mapping

| Acceptance item | Evidence | Result |
| --- | --- | --- |
| Backend focused tests pass | `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_business.py tests/gateway/test_config.py -- -q --tb=short` | PASS: 133 tests passed |
| Frontend auth/unit tests pass | `npm run test:auth` | PASS: 5 files / 30 tests passed |
| Frontend lint/build pass | `npm run lint`, `npm run typecheck`, `npm run build` | PASS |
| Gateway starts on VPS | Live VPS/systemd check intentionally not run because this Task 8 prompt says do not deploy; Task 7 docs provide systemd/runtime wiring and tests cover config bridge | NOT RUN — requires owner/VPS deploy check |
| Vercel deployment succeeds | Live Vercel deploy intentionally not run because this Task 8 prompt says do not deploy/push | NOT RUN — requires owner/Vercel deploy check |
| Telegram Web App opens for owner | Local auth/session and BFF tests cover valid owner initData; browser smoke covers outside-Telegram safe render; live Telegram launch not run | PARTIAL: automated/local PASS, live Telegram NOT RUN |
| Telegram Web App denies non-owner | `npm run test:auth` covers valid non-owner initData returning 403 and invalid/expired initData returning 401 | PASS locally |
| Owner can list chats | Backend dashboard API list tests, BFF route tests, UI list component tests, and build route table | PASS locally |
| Owner can open detail/history | Backend detail/history tests, BFF route tests, UI detail tests, `/chats/[token]` build route | PASS locally |
| Owner can request draft | Backend draft tests and reviewer-fix tests cover callback/no-callback behavior; BFF/client/UI tests cover action path | PASS locally |
| Owner can change mode | Backend mode tests, BFF/client/UI tests cover mode path and action state | PASS locally |
| No customer direct sends occur from `Generate draft now` | `test_draft_request_enqueues_latest_message_without_sending_customer_text`, `test_draft_request_without_enqueue_callback_returns_not_connected`, reviewer-fixes report; API returns queued only after injected callback success and never sends customer text itself | PASS locally |

## Known not-run live items / remaining production evidence

These were not run in this Task 8 pass because the delegated instruction explicitly said **do not deploy** and **do not push**:

- VPS `systemctl --user status hermes-gateway.service` after deploying/configuring the gateway.
- VPS dashboard API service start/restart and live logs against real service env.
- Vercel preview/production deployment.
- Telegram owner opening `/business`, tapping the Web App, and fetching real chat data through Vercel → VPS API.
- Non-owner live Telegram account denial through the deployed Web App.
- Real end-to-end mode/draft actions against live Business chats.

## Final verification status

Local final verification for Task 8 documentation/acceptance evidence is complete and green. Production readiness still depends on the explicitly not-run live deploy/TG/Vercel checks above.
