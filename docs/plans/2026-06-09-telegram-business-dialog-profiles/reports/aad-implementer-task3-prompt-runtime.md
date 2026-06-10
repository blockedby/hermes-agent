PI_RESULT: PASS
TASK: Task 3 prompt/session runtime foundation + relevant Task 9 profile lookup/cache context
TASK_PACKAGE: docs/plans/2026-06-09-telegram-business-dialog-profiles
REPORT_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task3-prompt-runtime.md
PROGRESS_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task3-prompt-runtime.md
COMMITS:
- 7c6a71812380d05846c6f39de7a913057cd1ac91: feat(telegram-business): add dialog profile prompt context
- f9323ff73dfedd14992e2515f5d2756f7bb22ddf: docs: report business prompt runtime implementation
FILES_CHANGED:
- gateway/session.py: added `SessionSource.business_context` and Telegram Business prompt block for owner/contact/Hermes participants, DB profile settings, customer metadata, and command/context safety wording.
- gateway/run.py: attaches current DB-backed Business dialog profile/customer/owner metadata to matching Telegram Business events before prompt/cache-significant context construction.
- gateway/platforms/telegram.py: wires `TelegramBusinessDialogProfileStore` into the Telegram adapter with a lazy accessor.
- tests/gateway/test_session.py: adds prompt tests for three participant roles, DB profile injection, metadata, owner-impersonation removal, command wording, and customer-text injection exclusion.
- tests/gateway/test_telegram_business.py: adds runtime profile lookup tests for matching dialog isolation and cache-significant prompt changes scoped to one dialog.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/plan.md: records Task 3 implementation evidence in the execution ledger.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task3-prompt-runtime.md: records implementation/test progress.
- progress.md: updates root worktree progress status and evidence.
AC_VERIFICATION:
- Business prompt says there are three participant roles owner/contact/Hermes: `test_telegram_business_prompt_frames_three_participants_and_db_profile` passed in container; prompt includes “Telegram Business dialog with three participant roles”, “Business owner/operator”, “Customer/contact”, and “Hermes assistant”.
- Prompt includes DB-stored assistant name/prefix and dialog_prompt/dialog_notes for the correct dialog: session and runtime tests passed; `test_business_runtime_attaches_matching_database_profile_only` confirms chat A profile prompt/notes appear and chat B settings do not.
- Prompt includes customer/contact name/username/user id/chat id metadata when available: session and runtime tests passed for name, `@username`, `User ID`, and `Chat ID`.
- Prompt removes/adjusts old owner-impersonation language, especially “do not speak as Hermes”: session test asserts old phrase is absent from Business prompt.
- Prompt explicitly says customer slash commands/control words are not Hermes commands: session test passed for exact prompt wording.
- Prompt explicitly says owner manual outgoing messages are authoritative context, not current customer requests: session test passed for prompt wording.
- Customer-authored text is never injected into system prompt as instructions: session negative test and runtime cache test passed; both assert synthetic customer prompt-injection/current-turn text is absent from generated system prompt.
- Chat A prompt does not include chat B settings: runtime test passed with two DB-backed profiles and asserts B prompt/notes excluded from A.
- Runtime reads current DB profile for matching Business event/dialog and profile changes affect only that dialog’s effective prompt/cache-significant context: `test_business_profile_change_affects_only_matching_dialog_prompt_signature` passed; updating chat A DB profile changes chat A prompt signature while chat B prompt/signature remains unchanged.
TESTS_RUN:
- `scripts/run_tests_docker.sh tests/gateway/test_session.py::TestBuildSessionContextPrompt::test_telegram_business_prompt_frames_three_participants_and_db_profile tests/gateway/test_session.py::TestBuildSessionContextPrompt::test_telegram_business_prompt_does_not_copy_customer_text_into_system_instructions tests/gateway/test_telegram_business.py::test_business_runtime_attaches_matching_database_profile_only tests/gateway/test_telegram_business.py::test_business_profile_change_affects_only_matching_dialog_prompt_signature -q`: not run to pytest; Docker image build failed before tests due PyPI/uv download connection reset for `rich==14.3.3`.
- Same `scripts/run_tests_docker.sh ... -q` retry: not run to pytest; Docker image build failed before tests due PyPI/uv download unexpected EOF for `aiohttp`.
- `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_session.py tests/gateway/test_telegram_business.py -- -q -k 'telegram_business_prompt or business_runtime_attaches_matching_database_profile_only or business_profile_change_affects_only_matching_dialog_prompt_signature'`: passed, 4 tests.
- `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_session.py tests/gateway/test_telegram_business.py`: passed, 175 tests.
QUALITY_CHECKS:
- `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m py_compile gateway/session.py gateway/run.py gateway/platforms/telegram.py`: passed.
- `git diff --check`: passed.
QUALITY_NOTES:
- Readability/reuse: reused existing `SessionSource`, `build_session_context_prompt`, Telegram Business registry/profile store, and existing agent cache signature behavior via the prompt string; no new dependency or broad abstraction added.
- Error handling/logging: profile attachment is best-effort with debug logging, matching gateway conventions for optional platform context; it does not block normal message handling on registry/profile read failure.
- Backend/API/data: uses the DB-backed `TelegramBusinessDialogProfileStore` as the prompt settings authority; runtime lookup uses dialog key from Business connection/customer chat/topic and does not read dashboard/API JSON settings for profile fields.
- Frontend/UI: not relevant; no dashboard UI changes in this delegated scope.
- DevOps/runtime: no env/config/deployment changes; canonical Docker rebuild was blocked by transient external package downloads, so existing-image container fallback was used.
- Security: no secrets/credentials logged; customer-authored current message text is intentionally excluded from `business_context` and system prompt construction.
- Concurrency/idempotency: runtime profile attachment reads current DB profile and creates a default only when missing; no global toolset/session mutation and no transcript rewrite.
- Compatibility/performance: preserves existing session key/cache mechanism; profile/settings affect cache via existing ephemeral prompt signature only for the matching session/dialog.
SIDE_FINDINGS:
- Blocking: none for delegated implementation; canonical Docker image rebuild had transient PyPI/uv download failures before pytest.
- Non-blocking follow-up candidates: owner may rerun `scripts/run_tests_docker.sh tests/gateway/test_session.py tests/gateway/test_telegram_business.py` once package downloads are healthy; other plan tasks remain for UI, bot buttons, prefix sends, mention invocation, and final integration.
PARENT_ACTION_REQUIRED:
- Action: none required for implementation handoff; optional owner verification can rerun canonical `scripts/run_tests_docker.sh tests/gateway/test_session.py tests/gateway/test_telegram_business.py` when PyPI connectivity is stable.
- Reason: canonical Docker rebuild failed before pytest due transient external download errors, not code/test failures.
- Expected evidence: Docker build completes and the two gateway test files pass.
- Safety bounds: run only the listed container command; do not use host pytest/npm/uv and stop if Docker build again fails before tests.
NOTES: Implementation evidence is provided; acceptance/done-state remains with the slice owner/auditor.
