PI_RESULT: PASS
TASK: Telegram Business dialog profiles — Task 5 Robot visible prefix on Business sends
TASK_PACKAGE: docs/plans/2026-06-09-telegram-business-dialog-profiles
REPORT_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task5-send-prefix.md
PROGRESS_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task5-send-prefix.md
COMMITS:
- 6be69d0e0: feat(telegram): prefix business sends
FILES_CHANGED:
- gateway/platforms/telegram.py: added DB-profile lookup and visible assistant prefix application before Telegram Business direct/approval send chunking.
- tests/gateway/test_telegram_business.py: injected in-memory profile store and added/updated focused Business send prefix tests.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task5-send-prefix.md: implementation progress/evidence notes.
AC_VERIFICATION:
- Default prefix is `🤖 Hermes:` when no per-dialog override exists: `test_business_auto_mode_sends_direct_customer_message` and existing approval send tests now assert default-prefixed sends — passed in container.
- Per-dialog prefix from DB is used: `test_business_auto_send_applies_database_prefix` and `test_business_approval_send_applies_database_prefix` use in-memory `TelegramBusinessDialogProfileStore` overrides — passed in container.
- Prefix is not duplicated: `test_business_send_does_not_double_prefix` — passed in container.
- Empty prefix disables visible prefix if owner explicitly configures it: `test_business_send_empty_database_prefix_disables_visible_prefix` — passed in container.
- Prefix works for both direct auto-send and approval-send: focused direct/approval tests plus full `tests/gateway/test_telegram_business.py` — passed in container.
- Preserve Telegram send/chunk length limits after prefixing: `test_business_send_preserves_chunk_limit_after_prefixing` asserts first prefixed chunk stays within `MAX_MESSAGE_LENGTH` by UTF-16 length — passed in container.
TESTS_RUN:
- RED attempt: `scripts/run_tests_docker.sh tests/gateway/test_telegram_business.py::test_business_auto_mode_sends_direct_customer_message ...` — failed before tests during Docker build dependency download (`google-api-core` connection reset).
- RED fallback container command: `docker run --rm -w /workspace -v "$PWD":/workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -k 'business_auto_mode_sends_direct_customer_message or business_auto_send_applies_database_prefix or business_send_does_not_double_prefix or business_send_empty_database_prefix_disables_visible_prefix or business_send_preserves_chunk_limit_after_prefixing or business_approval_send_applies_database_prefix'` — expected failure before production change: 2 passed, 4 failed.
- GREEN focused fallback container command: same `docker run ... scripts/run_tests.sh ... -k ...` — passed, 6 passed.
- Broader touched-file container command: `docker run --rm -w /workspace -v "$PWD":/workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py` — passed, 98 passed.
QUALITY_CHECKS:
- `docker run --rm -w /workspace -v "$PWD":/workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m ruff check gateway/platforms/telegram.py tests/gateway/test_telegram_business.py` — passed.
QUALITY_NOTES:
- Readability/reuse: reused `TelegramBusinessDialogProfileStore`, `TelegramBusinessChatRegistry.key`, existing direct-topic helpers, and existing `truncate_message(..., len_fn=utf16_len)` send chunking.
- Error handling/logging: profile lookup is best-effort with existing debug logging convention; send permission and Telegram send error behavior preserved.
- Backend/API/data: reads existing DB-backed profile by dialog key with default profile fallback; no schema/API changes or new writes on send-time fallback.
- Frontend/UI: not relevant.
- DevOps/runtime: added lazy/default profile store initialization in Telegram adapter; no env/Docker/deployment changes.
- Security: no secrets/PII logged; no auth/permission behavior changed.
- Concurrency/idempotency: send paths remain one send per computed chunk; no retry/idempotency semantics changed.
- Compatibility/performance: public send result shape preserved; one local SQLite profile lookup per Business send/approval send before chunking.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: repo Docker image rebuild was blocked by transient PyPI/network reset; existing local image with bind-mounted worktree provided container-only verification.
PARENT_ACTION_REQUIRED:
- Action: none.
- Reason: n/a.
- Expected evidence: n/a.
- Safety bounds: n/a.
NOTES: Existing untracked `docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/slice-owner-task5.md` was present before implementation and left untouched/uncommitted.
