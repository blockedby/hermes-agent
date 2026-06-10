PI_RESULT: PASS
TASK: Telegram Business dialog profiles — Task 10 mode/direct cleanup
TASK_PACKAGE: docs/plans/2026-06-09-telegram-business-dialog-profiles
REPORT_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task-10.md
PROGRESS_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task-10.md
COMMITS:
- 05bb42407d77a74ebcecc4c5c2aa5e3a6f25fb90: fix(telegram-business): fail closed direct sends without reply rights
FILES_CHANGED:
- gateway/platforms/telegram.py: added visible fail-closed owner/history notification for blocked Business direct sends; blocked inbound auto/mention_direct routing before enqueue when reply rights are false.
- gateway/platforms/telegram_business_history.py: added `outbound_failed` as a normalized Business history event type.
- tests/gateway/test_telegram_business.py: added focused can_reply=false tests for auto direct send and mention_direct one-shot behavior.
- tests/gateway/test_telegram_business_dashboard_api.py: extended dashboard draft test to prove no auto/direct marker is attached to queued draft events.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/plan.md: appended Task 10 execution ledger update.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task-10.md: recorded TDD/check progress.
AC_VERIFICATION:
- `watch`: notify/watch only — existing `test_telegram_business.py` coverage rerun in full touched gateway file; no changes to watch enqueue/direct behavior, and mention non-trigger paths still pass — passed.
- `draft`: approval draft only — existing draft/prefix/approval tests in `test_telegram_business.py` rerun; dashboard draft remains queue-only and no auto marker is attached — passed.
- `auto`: direct send only when `can_reply` allows — `test_business_auto_mode_sends_direct_customer_message` covers allowed direct send; new `test_business_auto_mode_can_reply_false_notifies_owner_and_records_history_without_customer_send` covers fail-closed false permission — passed.
- Dashboard draft request remains approval-safe (`sentToCustomer: false`) — `test_draft_request_enqueues_latest_message_without_sending_customer_text` asserts `sentToCustomer is False`, no customer text in response, and no `business_mode`/`business_invocation_mode` direct marker — passed.
- `mention_direct` direct sends as one-shot only when policy allows and does not change persistent mode — existing one-shot mention_direct test still passes; new can_reply=false mention_direct test asserts no enqueue and persistent mode remains `watch` — passed.
- `can_reply=false` fails closed and visibly notifies owner/history for direct-send and `mention_direct`; no hidden/customer-visible direct-send attempt treated as success — new tests assert owner notice uses owner chat without `business_connection_id`, history records `outbound_failed`/`business_reply_permission_disabled`, mention_direct does not enqueue, and auto send returns `success=False` — passed.
TESTS_RUN:
- RED: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q -k 'can_reply_false'` — failed as expected before implementation, 2 failed.
- GREEN focused: same `can_reply_false` container command — passed, 2 tests.
- Dashboard focused: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py -- -q -k 'draft_request_enqueues_latest_message_without_sending_customer_text'` — passed, 1 test.
- Targeted touched tests: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py -- -q` — passed, 2 files / 133 tests.
QUALITY_CHECKS:
- Compile: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m py_compile gateway/platforms/telegram.py gateway/platforms/telegram_business_dashboard_api.py gateway/platforms/telegram_business_history.py tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py` — passed, no output.
- Ruff: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m ruff check gateway/platforms/telegram.py gateway/platforms/telegram_business_dashboard_api.py gateway/platforms/telegram_business_history.py tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py` — passed, `All checks passed!`.
QUALITY_NOTES:
- Readability/reuse: reused existing Business reply-rights checks, owner notice conventions, and history append path; added one narrow helper for direct-send blocked visibility to avoid duplicating owner/history handling across inbound and send-time paths.
- Error handling/logging: fail-closed path preserves `SendResult(success=False, error="business_reply_permission_disabled", retryable=False)` for direct send; owner-notice send errors are logged and do not create customer sends.
- Backend/API/data: dashboard API contract preserved; history normalization now recognizes `outbound_failed` for direct-send failures.
- Frontend/UI: not relevant; no dashboard UI files changed.
- DevOps/runtime: no env, Docker, deployment, or startup wiring changes.
- Security: no secrets/logged credentials; blocked direct sends deliberately omit `business_connection_id` from Telegram customer send kwargs and notify only configured owner chat.
- Concurrency/idempotency: direct-send failure recording is best-effort per attempt, matching adjacent outbound history patterns; no retries or queued writes added.
- Compatibility/performance: existing modes/contracts preserved; permission check reuses cached/refresh logic and avoids LLM/enqueue work for inbound auto/mention_direct when direct reply is disallowed.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: no live Telegram API smoke was run; mocked Bot API contracts cover the delegated scope.
PARENT_ACTION_REQUIRED:
- Action: none.
- Reason: not applicable.
- Expected evidence: not applicable.
- Safety bounds: not applicable.
NOTES: `progress.md` was dirty before this task and was intentionally left uncommitted; the delegated prompt named it as an external progress file to preserve/update if useful.
