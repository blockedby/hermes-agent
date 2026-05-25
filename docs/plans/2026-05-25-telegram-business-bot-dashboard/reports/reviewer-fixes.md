PI_RESULT: PASS
TASK: Final reviewer required fixes — Telegram Business Dashboard epic
TASK_PACKAGE: docs/plans/2026-05-25-telegram-business-bot-dashboard
REPORT_PATH: docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/reviewer-fixes.md
PROGRESS_PATH: docs/plans/2026-05-25-telegram-business-bot-dashboard/progress/aad-implementer-reviewer-fixes.md
COMMITS:
- 954d4f60a: fix: harden telegram business dashboard API
FILES_CHANGED:
- gateway/platforms/telegram_business_dashboard_api.py: Enforced `X-Telegram-User-Id`, removed false standalone draft queueing, added injected latest-message enqueue behavior/status for draft/auto mode changes.
- tests/gateway/test_telegram_business_dashboard_api.py: Added regression coverage for actor header enforcement, standalone draft `503/not_connected`, mode enqueue callback/status, and no false queued state.
- apps/telegram-business-dashboard/src/lib/server/business-route.ts: Mapped nested Python API error shape `{error:{code,message}}` to existing public BFF errors.
- apps/telegram-business-dashboard/src/app/api/business/route-handlers.test.ts: Added nested `invalid_mode` and `missing_latest_message` BFF mapping coverage.
- docs/telegram-business-modes.md: Documented actor header enforcement and standalone/embedded enqueue behavior.
- docs/plans/2026-05-25-telegram-business-bot-dashboard/progress/browser-smoke.md: Moved root `progress.md` artifact into task package progress.
AC_VERIFICATION:
- Python draft request must not falsely return queued without enqueue callback: `test_draft_request_without_enqueue_callback_returns_not_connected` proves `503`/`not_connected`, no queued registry status, and no history draft event — passed.
- Python draft request with callback still queues real latest-message event: `test_draft_request_enqueues_latest_message_without_sending_customer_text` proves callback invocation with `reason="draft_request"`, no customer text in response, and queued status only after callback returns true — passed.
- Dashboard mode changes to draft/auto invoke callback or record no-enqueue: `test_mode_change_to_draft_invokes_latest_message_enqueue_callback` and `test_mode_change_to_auto_without_enqueue_callback_records_no_enqueue_status` prove callback invocation for `draft` and explicit `no_enqueue_callback` for standalone `auto` — passed.
- Next BFF handles nested Python API error shape: `route-handlers.test.ts` nested validation test proves `invalid_mode` and `missing_latest_message` are preserved for client-safe responses — passed.
- VPS API enforces `X-Telegram-User-Id`: `test_auth_requires_valid_telegram_user_header` proves missing/malformed actor headers reject before dashboard handling — passed.
- Root progress artifact handled: untracked root `progress.md` was moved to `docs/plans/2026-05-25-telegram-business-bot-dashboard/progress/browser-smoke.md` and committed — passed.
TESTS_RUN:
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py -- -q --tb=short`: RED failed as expected before implementation; GREEN passed, 15 tests.
- `cd apps/telegram-business-dashboard && npm run test:auth -- src/app/api/business/route-handlers.test.ts`: RED failed as expected before implementation; GREEN passed, 12 tests.
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_business.py -- -q --tb=short`: passed, 83 tests.
- `cd apps/telegram-business-dashboard && npm run test:auth`: passed, 5 files / 30 tests.
QUALITY_CHECKS:
- `venv/bin/python -m compileall -q gateway/platforms/telegram_business_dashboard_api.py tests/gateway/test_telegram_business_dashboard_api.py`: passed.
- `git diff --check`: passed.
- `cd apps/telegram-business-dashboard && npm run lint`: passed.
- `cd apps/telegram-business-dashboard && npm run typecheck`: passed.
- `cd apps/telegram-business-dashboard && npm run build`: passed; route table includes Business API routes.
QUALITY_NOTES:
- Readability/reuse: Reused existing dashboard service shape and Telegram latest-message event construction; callback remains injected/testable instead of adding new runtime dependencies.
- Error handling/logging: Preserved stable nested Python error shape and safe BFF mapping; no new logging added.
- Backend/API/data: Dashboard API now enforces documented actor header on all non-health endpoints; writes only record queued state after callback success; mode changes persist explicit enqueue status.
- Frontend/UI: No visible UI changed; BFF behavior covered by route-handler tests.
- DevOps/runtime: Docs clarify standalone API cannot enqueue live gateway work and must be embedded/injected for real queueing; no env names changed.
- Security: Bearer auth remains constant-time; actor header validation added; no secrets or customer message text logged/returned in draft responses.
- Concurrency/idempotency: Mode enqueue preserves existing latest-message fingerprint behavior to avoid duplicate enqueue claims for the same mode/message.
- Compatibility/performance: Success response shapes remain additive; no broad data scans or new dependencies added.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: Pre-existing untracked task-package browser artifacts remain (`reports/browser-smoke.md`, `verification/browser.md`, screenshots) because they were present before this fix and are not part of this implementation commit.
NOTES: No push performed.
