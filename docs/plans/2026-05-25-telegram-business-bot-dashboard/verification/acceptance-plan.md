## Task package
- Task name: Telegram Business Telegram Web App dashboard — final acceptance audit
- Task package: `docs/plans/2026-05-25-telegram-business-bot-dashboard/`
- Report path: `docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/acceptance-auditor.md`
- Acceptance plan path: `docs/plans/2026-05-25-telegram-business-bot-dashboard/verification/acceptance-plan.md`

## Acceptance criteria to audit
- Backend focused tests pass.
- Frontend lint/typecheck/build pass.
- Browser smoke shows the dashboard safely outside Telegram.
- `/business` launches the Web App when configured and falls back when not configured.
- The Telegram Web App auth/session flow rejects invalid or non-owner access.
- Owner can list chats, open detail/history, request draft, and change mode.
- No customer direct sends occur from `Generate draft now`.
- Live VPS/TG/Vercel deploy evidence is either present or explicitly marked not run.

## Evidence collected
- Fresh local checks from `verification/final.md`:
  - `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_business.py tests/gateway/test_config.py -- -q --tb=short` — passed (133 tests)
  - `cd apps/telegram-business-dashboard && npm run test:auth` — passed (30 tests)
  - `cd apps/telegram-business-dashboard && npm run lint` — passed
  - `cd apps/telegram-business-dashboard && npm run typecheck` — passed
  - `cd apps/telegram-business-dashboard && npm run build` — passed
- Browser evidence:
  - `docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/browser-smoke.md`
  - `docs/plans/2026-05-25-telegram-business-bot-dashboard/verification/browser.md`
  - screenshots in `docs/plans/2026-05-25-telegram-business-bot-dashboard/artifacts/screenshots/browser-smoke/2026-05-25T191123Z/`
- Functional evidence from `verification/final.md`:
  - dashboard API list/detail/history/mode/draft coverage
  - Telegram Business callback/approval/mode coverage
  - config bridge coverage for `telegram.business_dashboard_webapp_url`
  - no direct customer send from `Generate draft now`
- Explicitly not run:
  - VPS gateway/service live status
  - Vercel deployment smoke
  - live Telegram owner/non-owner launch flow

## Audit status
- Local implementation has enough evidence to accept the code path.
- Production/live deploy readiness still depends on the explicitly not-run VPS/TG/Vercel checks.
