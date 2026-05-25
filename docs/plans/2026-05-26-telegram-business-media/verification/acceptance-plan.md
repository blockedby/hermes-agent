# Acceptance plan: Telegram Business dashboard `Generate draft now`

## Target
- Scope: `apps/telegram-business-dashboard` chat detail UI/BFF plus `gateway/platforms/telegram_business_dashboard_api.py` draft endpoint.
- Outcome: Generate draft stays in the chat detail view, shows queued/generating/result state consistently, accepts optional empty/topic prompt, and avoids unintended redirect/refresh behavior.

## Acceptance criteria and evidence
- AC1: Generate draft stays in-place in chat detail UI.
  - Evidence to check: `chat-detail-shell.tsx` no longer clears detail state on success; `refreshDetailInPlace()` refreshes data without unmounting the detail; targeted dashboard UI/API tests.
- AC2: Queued / generating / result states are visible.
  - Evidence to check: `chat-detail-view.tsx` renders `Queueing draft...`, `Generating draft`, and `Draft request queued`; component render coverage in `business-dashboard-ui.test.tsx`.
- AC3: Optional prompt is accepted when present and omitted when blank.
  - Evidence to check: `generateBusinessDraft()` trims prompt and omits empty values; BFF route forwards `prompt`; backend stores prompt metadata/history; client + route-handler + Python API tests.
- AC4: Similar redirect/refresh regressions are audited out.
  - Evidence to check: dashboard buttons use `type="button"`; no stray `<form>` submit path in dashboard source.
- AC5: Evidence is fresh for the current diff.
  - Evidence to check: rerun targeted dashboard Vitest suite and `tests/gateway/test_telegram_business_dashboard_api.py` after current changes.

## Fresh verification run
- `cd apps/telegram-business-dashboard && npm run test:auth -- src/lib/business/business-api.test.ts src/app/api/business/route-handlers.test.ts src/components/business/business-dashboard-ui.test.tsx`
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py`

## Notes
- No live VPS/browser evidence was collected in this local audit; local acceptance is based on code inspection plus targeted tests.
- CI/remote checks are not available before push.
