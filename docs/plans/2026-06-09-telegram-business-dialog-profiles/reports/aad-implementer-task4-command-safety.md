PI_RESULT: PASS
TASK: Telegram Business customer slash-command safety (Task 4)
TASK_PACKAGE: docs/plans/2026-06-09-telegram-business-dialog-profiles
REPORT_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task4-command-safety.md
PROGRESS_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task4-command-safety.md

COMMITS:
- b6d2898b4: fix(gateway): block business customer slash commands

FILES_CHANGED:
- gateway/platforms/telegram.py: added Business text/caption slash-shape helper and used it before media preparation/agent enqueue.
- gateway/run.py: added early Business-shaped slash `MessageEvent` guard before pre-gateway/command hooks, command handlers, and active-session interrupt logic.
- tests/gateway/test_telegram_business.py: added adapter and gateway dispatch coverage for Task 4 negative and positive cases.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task4-command-safety.md: progress/evidence notes.
- /home/kcnc/code/hermes/hermes-agent/.worktrees/telegram-business-dialog-profiles/progress.md: external concise status summary updated (outside commit/worktree).

AC_VERIFICATION:
- Business customer `/new`, `/restart`, `/stop`, `/status`, `/help`, `/approve`, `/deny` do not run gateway command handlers: `test_gateway_blocks_business_customer_slash_commands_before_dispatch` parameterized coverage; command hook and handler mocks remain uncalled — passed.
- Business media caption `/restart` is ignored as a command: `test_business_media_caption_slash_command_is_ignored_before_agent` covers leading whitespace + `/restart@HermesBot` photo caption; no media preparation, enqueue, or customer send — passed.
- Active Business session receiving `/stop` is not interrupted through command logic: `test_gateway_business_stop_does_not_interrupt_active_session` verifies no `interrupt()` and no `_interrupt_and_clear_session()` — passed.
- Normal Telegram DM `/new` still works: `test_gateway_normal_telegram_dm_new_still_dispatches` verifies normal owner DM `/new` reaches reset handler — passed.
- Owner `/business` control command still works in owner chat: `test_gateway_owner_business_control_command_still_dispatches` verifies non-Business owner DM `/business` reaches business command handler — passed.
- Adapter edge cases: `test_business_customer_text_slash_command_is_ignored_before_agent` covers leading whitespace + bot suffix `/new@HermesBot`; caption test covers leading whitespace + suffix `/restart@HermesBot` — passed.

TESTS_RUN:
- RED (container, rebuilt image): `docker compose -f docker-compose.test.yml run --rm --build test bash -lc 'source "$HERMES_TEST_VENV/bin/activate" && python -m pytest tests/gateway/test_telegram_business.py -q -k "business_customer_text_slash_command_is_ignored_before_agent or business_media_caption_slash_command_is_ignored_before_agent or gateway_blocks_business_customer_slash_commands_before_dispatch or gateway_business_stop_does_not_interrupt_active_session or gateway_normal_telegram_dm_new_still_dispatches or gateway_owner_business_control_command_still_dispatches"'` — failed as expected before implementation: 9 failed, 3 passed, 81 deselected.
- GREEN focused (container): `docker compose -f docker-compose.test.yml run --rm test bash -lc 'source "$HERMES_TEST_VENV/bin/activate" && python -m pytest -q tests/gateway/test_telegram_business.py::test_business_customer_text_slash_command_is_ignored_before_agent tests/gateway/test_telegram_business.py::test_business_media_caption_slash_command_is_ignored_before_agent tests/gateway/test_telegram_business.py::test_gateway_blocks_business_customer_slash_commands_before_dispatch tests/gateway/test_telegram_business.py::test_gateway_business_stop_does_not_interrupt_active_session tests/gateway/test_telegram_business.py::test_gateway_normal_telegram_dm_new_still_dispatches tests/gateway/test_telegram_business.py::test_gateway_owner_business_control_command_still_dispatches'` — passed: 12 passed in 1.23s.
- Full targeted file (container repo runner): `docker compose -f docker-compose.test.yml run --rm test scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q` — passed: 93 tests passed, 0 failed.

QUALITY_CHECKS:
- `docker compose -f docker-compose.test.yml run --rm test bash -lc 'source "$HERMES_TEST_VENV/bin/activate" && python -m ruff check gateway/platforms/telegram.py gateway/run.py tests/gateway/test_telegram_business.py'` — passed: All checks passed.
- `git diff --check` — passed: no whitespace errors.
- Host pytest/npm/uv — not run per delegated container-only boundary.

QUALITY_NOTES:
- Readability/reuse: reused existing Business thread marker (`_is_telegram_business_source`) and existing adapter ignore branch; added only small local helpers.
- Error handling/logging: preserved existing logging convention; no new exception swallowing beyond existing ignore behavior.
- Backend/API/data: no persistence/schema/API changes; gateway command contract preserved for non-Business sources.
- Frontend/UI: not relevant.
- DevOps/runtime: no runtime config/env/container changes.
- Security: Business customer slash-like input is dropped before command/plugin-command dispatch; no secrets or sensitive payloads logged.
- Concurrency/idempotency: active-session `/stop` guard runs before running-agent interrupt logic for Business-shaped events.
- Compatibility/performance: normal Telegram DM `/new` and owner `/business` remain dispatchable; new checks are constant-time string/source checks.

SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: the pre-existing untracked `docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/slice-owner-task4.md` remained uncommitted because it was present before implementation and appears owner-owned.

PARENT_ACTION_REQUIRED:
- Action: none.
- Reason: not applicable.
- Expected evidence: not applicable.
- Safety bounds: not applicable.

NOTES: Scope kept to Task 4 command safety only. No profile DB, prompt settings, dashboard/UI, prefixing, invocation policy, or docs task work was implemented.
