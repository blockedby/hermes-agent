PI_RESULT: PASS
TASK: Task 3 — Hermes VPS Business Dashboard API
TASK_PACKAGE: docs/plans/2026-05-25-telegram-business-bot-dashboard
REPORT_PATH: docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/task-3-vps-api.md
PROGRESS_PATH: docs/plans/2026-05-25-telegram-business-bot-dashboard/progress/aad-implementer-task-3-vps-api.md
COMMITS:
- 3228303c2: feat: add telegram business dashboard API
FILES_CHANGED:
- gateway/platforms/telegram_business_dashboard_api.py: Added testable bearer-authenticated Business dashboard API service, optional aiohttp app/server entrypoint, view-model serialization, mode/draft/history/approval handlers, and bounded safe history placeholder store.
- tests/gateway/test_telegram_business_dashboard_api.py: Added focused backend tests for auth, list/detail filtering/sorting, mode changes, draft safety, invalid inputs, missing latest message, and corrupted-store fallback.
- docs/telegram-business-modes.md: Documented VPS API endpoints, bearer-token env vars, systemd example, reverse-proxy guidance, and draft-safety behavior.
- docs/plans/2026-05-25-telegram-business-bot-dashboard/progress/aad-implementer-task-3-vps-api.md: Progress and verification notes for the delegated implementation.
AC_VERIFICATION:
- Unauthorized/missing bearer token returns 401/403: `test_auth_rejects_missing_and_unknown_token` passed via focused gateway test run — passed.
- `GET chats` returns sorted/filterable view models hiding unnecessary internal IDs: `test_chats_list_is_filterable_sorted_and_hides_internal_ids` passed — passed.
- `GET chat detail` joins registry, approval counts, and history placeholder: `test_chat_detail_joins_approval_and_history_summary` passed — passed.
- `POST mode` changes mode and records actor metadata/history: `test_mode_change_updates_registry_and_records_actor_metadata` passed — passed.
- `POST draft` enqueues/marks request only and never sends customer text directly: `test_draft_request_enqueues_latest_message_without_sending_customer_text` passed; response asserts `sentToCustomer: false` and excludes latest text — passed.
- Invalid mode, unknown chat, and missing latest message are safe errors: `test_invalid_mode_and_unknown_chat_return_safe_errors` and `test_draft_request_requires_latest_message_context` passed — passed.
- Corrupted store safe behavior: `test_corrupted_stores_fail_closed_without_breaking_dashboard` passed — passed.
- Runtime/systemd/env wiring documented: `docs/telegram-business-modes.md` now documents `HERMES_DASHBOARD_API_TOKEN`, host/port env vars, systemd user unit, and HTTPS reverse-proxy guidance — passed by documentation inspection.
TESTS_RUN:
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py -- -q --tb=short`: initial RED failed with `ModuleNotFoundError` before implementation; later passed with 8 tests.
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_business.py -- -q --tb=short`: passed, 73 tests.
QUALITY_CHECKS:
- `venv/bin/python -m compileall -q gateway/platforms/telegram_business_dashboard_api.py tests/gateway/test_telegram_business_dashboard_api.py`: passed.
- `git diff --check`: passed.
QUALITY_NOTES:
- Readability/reuse: Reused `TelegramBusinessChatRegistry`, `TelegramBusinessApprovalStore`, existing `MessageEvent`/`SessionSource` shapes, and repo atomic-write helper; kept network layer optional and service methods directly testable.
- Error handling/logging: Store corruption follows adjacent fail-closed logging pattern and returns empty dashboard data instead of raising; API errors use stable JSON error codes/messages.
- Backend/API/data: API response models avoid raw Business connection/customer/topic IDs in chat list/detail; history placeholder is bounded and private-permission JSON; no schema migration required.
- Frontend/UI: Not relevant; frontend/BFF/UI explicitly out of scope.
- DevOps/runtime: Added env-based token/host/port and systemd/reverse-proxy docs; optional aiohttp app keeps dependency footprint aligned with existing patterns.
- Security: Bearer auth uses constant-time comparison; no secrets logged or committed; token is env/config injected; draft endpoint does not send customer text.
- Concurrency/idempotency: Writes reuse existing atomic replacement; draft requests record request metadata/fingerprint and only enqueue through injected callback or mark state.
- Compatibility/performance: Existing Telegram Business tests still pass; list operations are bounded to existing small JSON stores and sorted in memory for MVP.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: Wire the API service into the live gateway process if active in-memory draft enqueuing is required from the same long-running process; Task 6 can expand history instrumentation beyond the placeholder store.
NOTES: Local test wrapper picked `.venv` by default, but that venv lacks pytest. All successful pytest evidence used repo wrapper with `HERMES_TEST_VENV=$PWD/venv`.
