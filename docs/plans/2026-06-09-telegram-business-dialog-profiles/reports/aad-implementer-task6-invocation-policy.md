PI_RESULT: PASS
TASK: Task 6 — Telegram Business explicit safe invocation policy
TASK_PACKAGE: docs/plans/2026-06-09-telegram-business-dialog-profiles
REPORT_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task6-invocation-policy.md
PROGRESS_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task6-invocation-policy.md
COMMITS:
- b22ec789b: feat(telegram-business): add mention invocation policy
- 222284502: docs: add task6 invocation policy report
FILES_CHANGED:
- gateway/platforms/telegram.py: reads DB dialog profile `invocation_policy`, detects configured bot mentions, forces one-shot draft/auto routing without persisting mode, strips configured mention marker from queued text, and propagates one-shot mode into Business send metadata.
- gateway/platforms/base.py: preserves Telegram Business thread metadata and carries one-shot `business_mode` for adapter background delivery.
- gateway/run.py: carries one-shot `business_mode` through gateway thread metadata for synthetic/final sends.
- tests/gateway/test_telegram_business.py: TDD coverage for off/draft/direct policies, slash-with-mention blocking, case-insensitive mention punctuation/newline, configured/unknown username behavior, and one-shot metadata.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/verification/task6-invocation-policy.md: container-only verification evidence.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task6-invocation-policy.md: implementation progress notes.
AC_VERIFICATION:
- With `off`, mention does not override chat mode: `test_business_mention_policy_off_preserves_watch_mode` in targeted and broader container runs — passed.
- With `mention_draft`, mention queues approval-safe draft: `test_business_mention_draft_queues_approval_safe_draft_from_watch_mode` proves watch mode stays persisted and queued event is marked `draft` — passed.
- With `mention_direct`, mention sends direct response if reply permission allows: `test_business_mention_direct_marks_one_shot_direct_send_without_persisting_mode` proves watch mode is not persisted to auto, one-shot metadata is `business_mode=auto`, and `adapter.send()` uses the Business direct-send path when reply permission is allowed — passed.
- Mention path does not execute gateway slash commands: `test_business_slash_command_with_mention_is_blocked_even_when_invocation_enabled` plus existing gateway Business slash tests — passed.
- Normal mode behavior remains unchanged for non-mention customer messages: full `tests/gateway/test_telegram_business.py -- -q` remained green (107 tests), including existing watch/draft/auto mode tests — passed.
- Case-insensitive username match; mention with punctuation/newline is recognized: `test_business_mention_draft_queues_approval_safe_draft_from_watch_mode` uses `@HeRmEsBoT,\n` — passed.
- No known bot username fallback disabled or uses configured alias only: `test_business_mention_does_not_trigger_without_configured_bot_username` and `test_business_mention_does_not_trigger_when_bot_username_is_unknown` — passed.
TESTS_RUN:
- RED: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q -k 'mention or invocation or slash'`: failed as expected before implementation; 2 new mention policy failures.
- GREEN targeted: same command after implementation — passed, 16 selected tests.
- GREEN broader touched-file: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q` — passed, 107 tests.
QUALITY_CHECKS:
- `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m py_compile gateway/platforms/telegram.py gateway/platforms/base.py gateway/run.py tests/gateway/test_telegram_business.py` — passed.
- `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m ruff check gateway/platforms/telegram.py gateway/platforms/base.py gateway/run.py tests/gateway/test_telegram_business.py` — passed, `All checks passed!`.
QUALITY_NOTES:
- Readability/reuse: reused existing Telegram mention detection (`_message_mentions_bot`), DB profile store access patterns, mode routing, and send metadata helpers; no new dependencies.
- Error handling/logging: profile lookup failures follow existing debug-log/fallback pattern; slash-command blocking remains before mention invocation routing.
- Backend/API/data: reads existing SQLite profile settings only; no schema/migration/persisted mode changes. One-shot direct mode is carried on the event source/metadata and does not update the chat registry mode.
- Frontend/UI: not relevant; dashboard/buttons explicitly out of scope.
- DevOps/runtime: no env/config/deployment changes.
- Security: customer slash-like messages are still dropped before gateway command dispatch; mention routing only matches the configured bot username and does not fall back when username is unknown.
- Concurrency/idempotency: existing text enqueue/dedup/session behavior preserved; one-shot invocation marker is per event/source and not persisted.
- Compatibility/performance: normal Telegram DM slash behavior and owner `/business` controls untouched; profile lookup is a single local DB-store read on Business customer ingress.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: final Task 10 can further define can-reply-false visibility for `mention_direct`; current task proves direct path when reply permission is allowed.
PARENT_ACTION_REQUIRED:
- Action: none.
- Reason: n/a.
- Expected evidence: n/a.
- Safety bounds: n/a.
NOTES: No host pytest/npm/uv commands were run. Parent progress file `/home/kcnc/code/hermes/hermes-agent/.worktrees/telegram-business-dialog-profiles/progress.md` was appended with a brief Task 6 update.
