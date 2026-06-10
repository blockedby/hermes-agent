# Task 6 — Telegram Business invocation policy verification

## Scope

Container-only Python gateway verification for explicit safe Telegram Business mention invocation. No host pytest/npm/uv commands were run.

## TDD red evidence

Command:

```bash
docker run --rm -v "$PWD":/workspace -w /workspace \
  -e HERMES_TEST_VENV=/opt/hermes-test-venv \
  -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 \
  hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q -k 'mention or invocation or slash'
```

Result: failed as expected before production changes. New mention policy tests failed because mention messages in watch mode still sent watch notifications instead of queuing `mention_draft` / `mention_direct` events.

## Green evidence

Targeted command:

```bash
docker run --rm -v "$PWD":/workspace -w /workspace \
  -e HERMES_TEST_VENV=/opt/hermes-test-venv \
  -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 \
  hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q -k 'mention or invocation or slash'
```

Result: passed, 16 selected tests.

Broader touched-file command:

```bash
docker run --rm -v "$PWD":/workspace -w /workspace \
  -e HERMES_TEST_VENV=/opt/hermes-test-venv \
  -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 \
  hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q
```

Result: passed, 107 tests.

Compile/ruff command:

```bash
docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv \
  hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m py_compile \
  gateway/platforms/telegram.py gateway/platforms/base.py gateway/run.py tests/gateway/test_telegram_business.py

docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv \
  hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m ruff check \
  gateway/platforms/telegram.py gateway/platforms/base.py gateway/run.py tests/gateway/test_telegram_business.py
```

Result: passed; ruff output: `All checks passed!`.

## Acceptance evidence mapping

- `off` mention does not override mode: `test_business_mention_policy_off_preserves_watch_mode`.
- `mention_draft` queues approval-safe draft: `test_business_mention_draft_queues_approval_safe_draft_from_watch_mode`.
- `mention_direct` one-shot direct send path when reply permission allows: `test_business_mention_direct_marks_one_shot_direct_send_without_persisting_mode` plus `test_business_thread_metadata_includes_one_shot_invocation_mode`.
- Mention path does not execute slash commands: `test_business_slash_command_with_mention_is_blocked_even_when_invocation_enabled` and existing gateway slash blocking tests.
- Normal non-mention mode behavior unchanged: broader `tests/gateway/test_telegram_business.py` run remains green, including existing watch/draft/auto/slash safety tests.
- Case-insensitive username and punctuation/newline recognition: `test_business_mention_draft_queues_approval_safe_draft_from_watch_mode` (`@HeRmEsBoT,\n`).
- No fallback when bot username is unknown or different from configured username: `test_business_mention_does_not_trigger_without_configured_bot_username` and `test_business_mention_does_not_trigger_when_bot_username_is_unknown`.
