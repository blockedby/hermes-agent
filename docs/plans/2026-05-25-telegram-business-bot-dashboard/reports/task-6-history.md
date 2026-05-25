PI_RESULT: PASS
TASK: Task 6 - Bounded Business history store and instrumentation
TASK_PACKAGE: docs/plans/2026-05-25-telegram-business-bot-dashboard
REPORT_PATH: docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/task-6-history.md
PROGRESS_PATH: docs/plans/2026-05-25-telegram-business-bot-dashboard/progress/aad-implementer-task-6-history.md
COMMITS:
- f3be21ea1b4a541edcd29ecd08b2d4bea8263ba8: feat: record telegram business dashboard history
FILES_CHANGED:
- gateway/platforms/telegram_business_history.py: new private bounded JSON history store with atomic writes, corrupt-file fallback, event normalization, preview truncation, per-chat pruning, and cursor pagination.
- gateway/platforms/telegram_business_dashboard_api.py: uses the standalone history store and exposes bounded `/history` pages with `nextCursor`.
- gateway/platforms/telegram.py: best-effort history instrumentation for inbound Business messages, mode changes, draft requests, owner approval creation/sent/cancelled/failed/partial states, outbound auto sends, and watch-rule matches.
- tests/gateway/test_telegram_business_dashboard_api.py: focused history store/API tests for append/load/prune/truncate/corrupt/pagination.
- tests/gateway/test_telegram_business.py: adapter lifecycle evidence for inbound/rule events and mode-change draft request history.
- docs/plans/2026-05-25-telegram-business-bot-dashboard/progress/aad-implementer-task-6-history.md: implementation progress and command evidence.
AC_VERIFICATION:
- History is bounded per chat and private on disk: `test_history_store_normalizes_prunes_truncates_and_paginates` passed; asserts max-3 pruning and `0600` file permissions.
- History API returns newest/relevant events with pagination/cursor: `test_history_endpoint_returns_bounded_pages_with_cursor` passed; asserts newest-first pages and `nextCursor`.
- Long previews are truncated: `test_history_store_normalizes_prunes_truncates_and_paginates` passed; asserts normalized preview length <= 500 and control-char removal.
- Corrupt history file does not break dashboard: `test_history_store_corrupt_file_falls_back_safely` and existing corrupted-store API test passed.
- Adapter/API lifecycle evidence: `test_business_update_records_inbound_and_rule_history`, mode callback history assertion, and dashboard API mode/draft tests passed.
TESTS_RUN:
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_business.py -- -q --tb=short -k 'history_store_normalizes or business_update_records_inbound'`: passed, 2 tests.
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_business.py -- -q --tb=short`: passed, 77 tests.
QUALITY_CHECKS:
- `venv/bin/python -m py_compile gateway/platforms/telegram_business_history.py gateway/platforms/telegram_business_dashboard_api.py gateway/platforms/telegram.py tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_business.py`: passed.
- `git diff --check`: passed.
QUALITY_NOTES:
- Readability/reuse: store follows existing registry/approval JSON-store style and reuses `atomic_replace`/`get_hermes_home` patterns; instrumentation is local best-effort helper calls.
- Error handling/logging: corrupt history loads return `{}` with error log; adapter history append failures are debug-only and do not block message/approval flow.
- Backend/API/data: persisted shape remains versioned JSON under Telegram platform directory; history API preserves existing auth and adds cursor metadata without exposing internal chat IDs.
- Frontend/UI: not relevant.
- DevOps/runtime: no new env vars, services, migrations, or dependencies.
- Security: private directory/file perms (`0700`/`0600`); no secrets/tokens added to history events; previews are bounded.
- Concurrency/idempotency: writes are atomic; mode callback records `mode_changed` only for actual mode transitions while draft enqueue dedupe remains in place.
- Compatibility/performance: per-chat history bounded to 50 events; dashboard API import still exposes `TelegramBusinessHistoryStore` through imported module symbol while the canonical module is standalone.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: default `.venv` in this checkout lacks pytest, so local checks required `HERMES_TEST_VENV=$PWD/venv`.
NOTES: Did not push. Owner/auditor should decide final acceptance; this report only records implementation evidence.
