# Verification: Telegram Business dashboard draft behavior

Date: 2026-05-26
Scope: dashboard Generate draft now in-place UI/API behavior and optional prompt pass-through.

## Acceptance matrix

- AC1: Generate draft does not navigate/refresh or lose chat-detail context.
  - Covered by: code audit and targeted UI test.
  - Result: passed.
  - Evidence: `chat-detail-view.tsx` Generate button is `type="button"` and calls `onGenerateDraft`; `chat-detail-shell.tsx` no longer calls `loadDetail()` after success (which forced `status="loading"` and temporarily unmounted detail content), and instead uses `refreshDetailInPlace()` without clearing current detail state. `npm run test:auth -- ...business-dashboard-ui.test.tsx` passed.

- AC2: UI shows queued/submitting/result/error state.
  - Covered by: UI state/code audit and component render test.
  - Result: passed.
  - Evidence: action status renders `Generating draft` while loading, `Draft request queued` on success, and `Action failed` on recoverable error; button label changes to `Queueing draft...` while disabled. Targeted Vitest suite passed.

- AC3: Empty prompt valid; non-empty prompt passes through to backend/draft generation path.
  - Covered by: client API test, BFF route test, Python dashboard API test.
  - Result: passed.
  - Evidence: `generateBusinessDraft()` trims prompt and omits empty prompts; BFF forwards `prompt`; backend stores prompt in event metadata/channel context/history/response. Commands below passed.

- AC4: Related dashboard controls audited for unintended redirect/refresh behavior.
  - Covered by: grep/code audit for `<form` and `Button` controls under `apps/telegram-business-dashboard/src/components/business`.
  - Result: passed.
  - Evidence: no `<form` in dashboard source; all Business dashboard `Button` controls in `chat-detail-view.tsx` and `dashboard-view.tsx` now specify `type="button"`.

- AC5: Targeted tests/checks prove behavior and no obvious regression in existing draft endpoints.
  - Covered by: dashboard Vitest tests, typecheck, lint, Python dashboard API tests.
  - Result: passed, after environment retry for Python venv.
  - Evidence: commands below.

## Commands run

- `cd apps/telegram-business-dashboard && npm run test:auth -- src/lib/business/business-api.test.ts src/app/api/business/route-handlers.test.ts src/components/business/business-dashboard-ui.test.tsx`
  - Result: passed; 3 files, 19 tests passed.
- `cd apps/telegram-business-dashboard && npm run typecheck`
  - Result: passed.
- `cd apps/telegram-business-dashboard && npm run lint`
  - Result: passed.
- `scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py -q`
  - Result: failed before tests; repo wrapper's per-file runner does not accept `-q` in this mode.
- `scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py`
  - Result: failed before tests; `.venv` lacks pytest (`No module named pytest`).
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py`
  - Result: passed; 15 tests passed.

## Browser/manual evidence

Not run locally. The changed behavior is covered by component/API tests and code-level evidence; no live Telegram Web App runtime was available or requested, and deployment to VPS is explicitly out of scope.

## Root owner rerun (2026-05-26)

- `cd apps/telegram-business-dashboard && npm run test:auth -- src/lib/business/business-api.test.ts src/app/api/business/route-handlers.test.ts src/components/business/business-dashboard-ui.test.tsx && npm run typecheck && npm run lint`
  - Result: passed (`3` Vitest files / `19` tests; typecheck and lint exited 0).
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py`
  - Result: passed (`15` tests).
