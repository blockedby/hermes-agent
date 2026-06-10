PI_RESULT: PASS
TASK: Task 2: Dashboard backend settings API uses DB store
TASK_PACKAGE: docs/plans/2026-06-09-telegram-business-dialog-profiles
REPORT_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task2-backend-settings-api.md
PROGRESS_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task2-backend-settings-api.md
COMMITS:
- 49f13ccd110ec853ee83e2e478d3afae5c75b05e: feat(telegram-business): add dashboard settings API
- report artifact commit: created after this report was written; see final implementer response for SHA.
FILES_CHANGED:
- gateway/platforms/telegram_business_dashboard_api.py: injected DB profile store dependency; added GET/PATCH settings dispatch, camelCase/snake_case mapping, store validation/persistence, settings_changed history event, and aiohttp settings route registration.
- gateway/platforms/telegram_business_history.py: allowed `settings_changed` history events so successful settings changes keep their event type.
- tests/gateway/test_telegram_business_dashboard_api.py: added Task 2 settings API tests using in-memory SQLite profile store and no JSON source-of-truth assertions.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task2-backend-settings-api.md: progress notes and check milestones.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/verification/task2-backend-settings-api.md: RED/GREEN and quality evidence.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task2-backend-settings-api.md: final implementation report.
AC_VERIFICATION:
- GET settings returns defaults for an existing Business chat before explicit save: `test_get_chat_settings_returns_database_defaults` passed; endpoint upserts default profile through injected DB store and response returns normalized camelCase settings — passed.
- PATCH settings persists to DB and returns normalized settings: `test_patch_chat_settings_persists_to_database_and_history` passed; asserts snake_case DB fields and camelCase response for display name, emoji prefix, empty prompt, notes, and invocation policy — passed.
- PATCH settings does not mutate mode/latest-message/customer metadata nor store settings in business_chats JSON: same test compares registry metadata before/after and asserts no JSON settings/profile fields are added — passed.
- Unknown token returns 404: `test_chat_settings_unknown_chat_returns_404` passed for GET and PATCH — passed.
- Missing/invalid auth remains rejected: existing dashboard auth tests passed after the new constructor dependency was added; auth still runs before settings dispatch — passed.
- Invalid values return 400: `test_patch_chat_settings_rejects_invalid_invocation_policy` passed; invalid policy returns `invalid_settings`, DB default remains `off`, and no history event is written — passed.
- Successful change records `settings_changed` history event with actor id: `test_patch_chat_settings_persists_to_database_and_history` passed; history event type and `actor_user_id` are preserved — passed.
TESTS_RUN:
- `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py`: passed, 19 passed / 0 failed.
- `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_business_profiles.py`: passed, 31 passed / 0 failed.
- RED evidence: same bind-mounted container command failed before implementation with `BusinessDashboardAPI.__init__() got an unexpected keyword argument 'profile_store'` after new tests were added.
QUALITY_CHECKS:
- `docker run --rm -v "$PWD":/workspace -w /workspace ... hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m py_compile gateway/platforms/telegram_business_dashboard_api.py gateway/platforms/telegram_business_history.py gateway/platforms/telegram_business_profiles.py`: passed (no output).
- `docker run --rm -v "$PWD":/workspace -w /workspace ... hermes-agent:test-runner /opt/hermes-test-venv/bin/ruff check gateway/platforms/telegram_business_dashboard_api.py gateway/platforms/telegram_business_history.py tests/gateway/test_telegram_business_dashboard_api.py`: passed (`All checks passed!`).
- `git diff --check -- gateway/platforms/telegram_business_dashboard_api.py gateway/platforms/telegram_business_history.py tests/gateway/test_telegram_business_dashboard_api.py docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task2-backend-settings-api.md`: passed (no output).
QUALITY_NOTES:
- Readability/reuse: reused existing `BusinessDashboardAPI.handle_request()`, `_coerce_body()`, `_error()`, history append style, and `TelegramBusinessDialogProfileStore` validation/update methods; added only small local mapping/view helpers.
- Error handling/logging: preserved existing structured API error shape; store `ValueError` maps to 400 `invalid_settings`; no new logging added.
- Backend/API/data: settings source of truth is the DB profile store; GET upserts defaults for registry chat entries; PATCH writes only through `update_by_token()` validation path; no migration/schema change beyond existing Task 1 store.
- Frontend/UI: not relevant; frontend/UI was out of scope.
- DevOps/runtime: aiohttp route `/api/business/chats/{token}/settings` registered; no env/config/deployment changes.
- Security: existing bearer auth and `X-Telegram-User-Id` actor validation remain before endpoint dispatch; no secrets/PII logging added.
- Concurrency/idempotency: PATCH follows existing simple store write pattern; GET upsert is safe for default profile creation; no queue/retry behavior changed.
- Compatibility/performance: existing endpoints/tests remain green; settings join is separate endpoint and does not add registry JSON writes or expensive list-path DB work.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: a full rebuilt Docker image check could be rerun by the owner if PyPI connectivity is stable; this implementation used a container-only bind-mounted fallback because the rebuild hit a transient PyPI `jinja2` connection reset.
PARENT_ACTION_REQUIRED:
- Action: none.
- Reason: not applicable.
- Expected evidence: not applicable.
- Safety bounds: not applicable.
NOTES: Pre-existing/concurrent dirty files were left untouched and uncommitted: root `progress.md`, `gateway/session.py`, `tests/gateway/test_session.py`, `tests/gateway/test_telegram_business.py`, and `docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task3-prompt-runtime.md`.
