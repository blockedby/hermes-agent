# Task 2 backend settings API verification

## Scope

Backend Python `BusinessDashboardAPI` settings GET/PATCH behavior using injected/in-memory `TelegramBusinessDialogProfileStore`/SQLite. Host pytest/npm/uv were not used.

## RED evidence

- `HERMES_DOCKER_BUILD=0 scripts/run_tests_docker.sh tests/gateway/test_telegram_business_dashboard_api.py -q`
  - Result: failed before pytest because `run_tests_parallel.py` does not accept `-q`.
- `HERMES_DOCKER_BUILD=0 scripts/run_tests_docker.sh tests/gateway/test_telegram_business_dashboard_api.py`
  - Result: stale no-build image did not include current worktree tests (15 tests), so not valid RED evidence.
- `scripts/run_tests_docker.sh tests/gateway/test_telegram_business_dashboard_api.py`
  - Result: Docker rebuild failed before tests on transient PyPI download error for `jinja2==3.1.6` (`connection reset`).
- Container-only current-source RED fallback:
  ```bash
  docker run --rm \
    -v "$PWD":/workspace \
    -w /workspace \
    -e HERMES_TEST_VENV=/opt/hermes-test-venv \
    -e HERMES_TEST_WORKERS=4 \
    -e TZ=UTC \
    -e LANG=C.UTF-8 \
    -e LC_ALL=C.UTF-8 \
    -e PYTHONHASHSEED=0 \
    hermes-agent:test-runner \
    scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py
  ```
  - Result: 17 failed, 2 passed.
  - Expected failure excerpt: `TypeError: BusinessDashboardAPI.__init__() got an unexpected keyword argument 'profile_store'`.

## GREEN / quality evidence

- Targeted Task 2 dashboard API tests:
  ```bash
  docker run --rm \
    -v "$PWD":/workspace \
    -w /workspace \
    -e HERMES_TEST_VENV=/opt/hermes-test-venv \
    -e HERMES_TEST_WORKERS=4 \
    -e TZ=UTC \
    -e LANG=C.UTF-8 \
    -e LC_ALL=C.UTF-8 \
    -e PYTHONHASHSEED=0 \
    hermes-agent:test-runner \
    scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py
  ```
  - Result after implementation/fix: 19 passed, 0 failed.

- Adjacent backend store/API tests:
  ```bash
  docker run --rm \
    -v "$PWD":/workspace \
    -w /workspace \
    -e HERMES_TEST_VENV=/opt/hermes-test-venv \
    -e HERMES_TEST_WORKERS=4 \
    -e TZ=UTC \
    -e LANG=C.UTF-8 \
    -e LC_ALL=C.UTF-8 \
    -e PYTHONHASHSEED=0 \
    hermes-agent:test-runner \
    scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_business_profiles.py
  ```
  - Result: 31 passed, 0 failed.

- Syntax compile:
  ```bash
  docker run --rm \
    -v "$PWD":/workspace \
    -w /workspace \
    -e HERMES_TEST_VENV=/opt/hermes-test-venv \
    -e TZ=UTC \
    -e LANG=C.UTF-8 \
    -e LC_ALL=C.UTF-8 \
    -e PYTHONHASHSEED=0 \
    hermes-agent:test-runner \
    /opt/hermes-test-venv/bin/python -m py_compile gateway/platforms/telegram_business_dashboard_api.py gateway/platforms/telegram_business_history.py gateway/platforms/telegram_business_profiles.py
  ```
  - Result: passed (no output).

- Ruff lint on scoped files:
  ```bash
  docker run --rm \
    -v "$PWD":/workspace \
    -w /workspace \
    -e HERMES_TEST_VENV=/opt/hermes-test-venv \
    -e TZ=UTC \
    -e LANG=C.UTF-8 \
    -e LC_ALL=C.UTF-8 \
    -e PYTHONHASHSEED=0 \
    hermes-agent:test-runner \
    /opt/hermes-test-venv/bin/ruff check gateway/platforms/telegram_business_dashboard_api.py gateway/platforms/telegram_business_history.py tests/gateway/test_telegram_business_dashboard_api.py
  ```
  - Result: `All checks passed!`

- Whitespace check:
  ```bash
  git diff --check -- gateway/platforms/telegram_business_dashboard_api.py gateway/platforms/telegram_business_history.py tests/gateway/test_telegram_business_dashboard_api.py docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task2-backend-settings-api.md
  ```
  - Result: passed (no output).

## Acceptance evidence mapping

- GET settings returns defaults for existing Business chat before explicit save: `test_get_chat_settings_returns_database_defaults` passed; asserts DB profile is upserted and registry JSON has no `settings` field.
- PATCH settings persists to DB and returns normalized settings: `test_patch_chat_settings_persists_to_database_and_history` passed; asserts camelCase response and snake_case DB values.
- PATCH settings does not mutate mode/latest-message/customer metadata nor store settings in JSON registry: same test passed; compares registry entry metadata before/after and asserts no settings/source fields in registry entry.
- Unknown token returns 404: `test_chat_settings_unknown_chat_returns_404` passed for GET and PATCH.
- Missing/invalid auth remains rejected: existing dashboard auth tests passed with the new constructor default profile store.
- Invalid values return 400: `test_patch_chat_settings_rejects_invalid_invocation_policy` passed; default DB profile remains `off` and no history event is appended.
- Successful change records `settings_changed` history event with actor id: `test_patch_chat_settings_persists_to_database_and_history` passed; `settings_changed` was added to the history store allowlist so the event type is preserved.
