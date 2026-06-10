PI_RESULT: PASS
TASK: Wave 1 Task 1 — DB-backed Telegram Business dialog profile store
TASK_PACKAGE: docs/plans/2026-06-09-telegram-business-dialog-profiles
REPORT_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task-1-db-profile-store.md
PROGRESS_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task-1-db-profile-store.md
COMMITS:
- bda44fece4f3: feat(telegram): add business dialog profile store
FILES_CHANGED:
- gateway/platforms/telegram_business_profiles.py: added SQLite-backed `TelegramBusinessDialogProfileStore`, schema creation, default profile generation, token/key lookup, upsert/update/clear methods, invocation policy normalization, deterministic text/control-character validation, and profile-aware default DB path.
- tests/gateway/test_telegram_business_profiles.py: added in-memory/injected-connection storage tests covering defaults, updates, token lookup, invalid policy rejection, length bounds, empty prompt clearing, control stripping, unknown token behavior, and default path construction.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task-1-db-profile-store.md: recorded implementation progress and verification evidence.
AC_VERIFICATION:
- Store creates schema in an in-memory DB: `test_profile_store_upserts_default_profile_in_memory_db` inspects `sqlite_master` after `TelegramBusinessDialogProfileStore(db_path=":memory:")` — passed.
- Upsert with a chat entry creates default settings: same test upserts a missing-topic entry and asserts default assistant name/prefix, empty prompt/notes, `off` policy, and dialog key/token fields — passed.
- Update persists `assistant_display_name`, `assistant_prefix`, `dialog_prompt`, `dialog_notes`, `invocation_policy`: `test_profile_store_updates_prompt_prefix_and_invocation_policy` updates by token and reads back by key — passed.
- Invalid invocation policy is rejected before persistence: `test_profile_store_rejects_unknown_invocation_policy_before_persistence` asserts `notify` normalizes to `None`, update raises `ValueError`, and stored policy remains `off` — passed.
- Length bounds are enforced deterministically: `test_profile_store_rejects_overlong_text_fields_before_persistence` rejects overlong `assistant_display_name`, `assistant_prefix`, `dialog_prompt`, and `dialog_notes` with `ValueError` and verifies prior values remain unchanged; storage boundary choice is rejection, not truncation — passed.
- Profile can be found by dialog key and token: default/update tests assert `get_by_key`; `test_profile_store_get_by_token_returns_same_profile` uses an injected `sqlite3.Connection` and asserts token lookup returns the same profile — passed.
- No writes go to `~/.hermes` in tests: in-memory tests use `db_path=":memory:"` or injected connection; default-home usage is monkeypatched to raise in the in-memory default-upsert test; the default path test monkeypatches `get_hermes_home()` to `tmp_path` — passed.
TESTS_RUN:
- `scripts/run_tests_docker.sh tests/gateway/test_telegram_business_profiles.py -q`: failed before collection because the repository Docker runner does not accept `-q` (`run_tests_parallel.py: error: unrecognized arguments: -q`); rerun without `-q`.
- `HERMES_DOCKER_BUILD=0 scripts/run_tests_docker.sh tests/gateway/test_telegram_business_profiles.py`: RED failed as expected before implementation with `ModuleNotFoundError: No module named 'gateway.platforms.telegram_business_profiles'`.
- `scripts/run_tests_docker.sh tests/gateway/test_telegram_business_profiles.py`: GREEN passed after implementation, `8/8` tests.
- `scripts/run_tests_docker.sh tests/gateway/test_telegram_business_profiles.py`: final targeted run after API/bounds coverage polish passed, `11/11` tests.
QUALITY_CHECKS:
- `docker run --rm hermes-agent:test-runner /opt/hermes-test-venv/bin/ruff check gateway/platforms/telegram_business_profiles.py tests/gateway/test_telegram_business_profiles.py`: passed (`All checks passed!`).
- Broader pytest/build/npm/uv checks: not run by scope; prompt limited verification to storage unit tests and prohibited host pytest/npm/uv.
QUALITY_NOTES:
- Readability/reuse: Store is a focused platform-local module; reused `TelegramBusinessChatRegistry.key()` and `token_for_key()` rather than duplicating dialog key/token derivation.
- Error handling/logging: Validation rejects unsupported fields, unknown invocation policies, and overlong text before SQLite writes; no new logging added.
- Backend/API/data: Schema matches planned fields/index; source of truth is SQLite; tests cover in-memory DB and injected connection. No API/runtime/dashboard integration was added by boundary.
- Frontend/UI: Not relevant; no frontend touched.
- DevOps/runtime: Default DB path is profile-aware via `get_hermes_home() / gateway/platforms/telegram/business_profiles.db`; no deployment/container/CI config changed.
- Security: No secrets or sensitive payloads logged; tests avoid real `~/.hermes`; control characters are stripped from stored text fields while normal Unicode is preserved.
- Concurrency/idempotency: Upsert uses SQLite `ON CONFLICT(dialog_key)` so repeat chat-entry upserts are idempotent for a dialog key; no queue/job concurrency touched.
- Compatibility/performance: Additive module and tests only; token index exists for lookup; no existing public API or runtime path changed.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: Later integration tasks should inject this store into dashboard/runtime layers instead of reading JSON chat registry for dialog profile settings.
PARENT_ACTION_REQUIRED:
- Action: none.
- Reason: none.
- Expected evidence: none.
- Safety bounds: none.
NOTES: Implementation stayed storage-only. Tests use in-memory SQLite or a supplied `sqlite3.Connection`; the only filesystem DB construction test uses a monkeypatched `tmp_path` home.
