## Task
- Mission: Implement Task 10, Auto/draft/direct behavior cleanup and evidence.
- Target: Telegram Business mode/direct routing and dashboard draft safety.
- Boundaries: No broad refactors; use existing mode/invocation code; container-only verification.
- Done when: watch/draft/auto/dashboard-draft/mention_direct semantics are tested, and can_reply=false fails closed with owner/history visibility for direct-send/mention_direct.

## Context
- Task package: `/home/kcnc/code/hermes/hermes-agent/.worktrees/telegram-business-dialog-profiles/docs/plans/2026-06-09-telegram-business-dialog-profiles`
- Worktree: `/home/kcnc/code/hermes/hermes-agent/.worktrees/telegram-business-dialog-profiles`
- Branch: `feat/telegram-business-dialog-profiles`
- PR: https://github.com/blockedby/hermes-agent/pull/25
- Implementer report: `docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task-10.md`

## Ownership model
- Slice stayed whole under this slice owner.
- Implementation was delegated to one `aad-implementer` task.
- No sub-slices were created.

## Changes / commits
- `05bb42407d77a74ebcecc4c5c2aa5e3a6f25fb90` — `fix(telegram-business): fail closed direct sends without reply rights`
- `bf0d783a534059baa0f964ba17f0435181535e00` — `docs: report task10 mode direct cleanup`

Changed files:
- `gateway/platforms/telegram.py`
- `gateway/platforms/telegram_business_history.py`
- `tests/gateway/test_telegram_business.py`
- `tests/gateway/test_telegram_business_dashboard_api.py`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/plan.md`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task-10.md`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task-10.md`
- External requested progress updated, uncommitted: `/home/kcnc/code/hermes/hermes-agent/.worktrees/telegram-business-dialog-profiles/progress.md`

## Acceptance verification
- watch: notify/watch only — covered by rerun of `tests/gateway/test_telegram_business.py`; passed.
- draft: approval draft only — covered by rerun of Telegram Business tests and dashboard draft test; passed.
- auto: direct-send only when `can_reply` allows — existing allowed-send tests plus new can_reply=false tests; passed.
- dashboard draft request remains `sentToCustomer: false` — dashboard API test extended to assert no auto/direct marker; passed.
- mention_direct one-shot only, no persistent mode change — existing one-shot coverage plus new can_reply=false mention_direct test; passed.
- can_reply=false fail-closed visibility/history — new tests assert no customer send/enqueue, owner notice, and `outbound_failed` history with `business_reply_permission_disabled`; passed.

## Exact container tests run
Implementer TDD / checks:
- RED: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q -k 'can_reply_false'` — failed as expected before implementation, 2 failed.
- GREEN: same `can_reply_false` command — passed, 2 tests.
- `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py -- -q -k 'draft_request_enqueues_latest_message_without_sending_customer_text'` — passed, 1 test.
- `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py -- -q` — passed, 2 files / 133 tests.
- `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m py_compile gateway/platforms/telegram.py gateway/platforms/telegram_business_dashboard_api.py gateway/platforms/telegram_business_history.py tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py` — passed.
- `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m ruff check gateway/platforms/telegram.py gateway/platforms/telegram_business_dashboard_api.py gateway/platforms/telegram_business_history.py tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py` — passed.

Owner fresh verification:
- `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py -- -q` — passed, 2 files / 133 tests.

## Issues
- R-01: can_reply=false direct paths were ambiguous/under-visible.
  - Resolution: direct-send/auto/mention_direct fail closed, notify owner when configured, and record `outbound_failed` history with `business_reply_permission_disabled`.
- Follow-ups: none for this Task 10 scope.
- Unresolved blockers: none.

## Verdict
- Status: success.
- Goal state: fully achieved for Task 10.
- System readiness: ready for parent integration/final slice checks, with no live Telegram API smoke run by design; mocked Bot API contracts cover this delegated scope.
