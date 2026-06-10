## Task
- Mission: Implement Task 3 plus relevant Task 9 foundation for Telegram Business participant prompt/runtime DB profile lookup.
- Target: `gateway/session.py`, `gateway/run.py`, `gateway/platforms/telegram.py`, `tests/gateway/test_session.py`, `tests/gateway/test_telegram_business.py`.
- Boundaries: Kept scope to prompt/runtime profile lookup. Did not implement dashboard UI, bot buttons, prefix send, or mention invocation.
- Done when: Business system prompt uses explicit owner/contact/Hermes participant framing, injects only matching DB-backed dialog settings, excludes customer text as system instructions, and runtime profile changes affect only the matching dialog prompt/cache-significant context.

## Context
- Slice: Telegram Business dialog profiles / participant prompt runtime.
- Task package: `docs/plans/2026-06-09-telegram-business-dialog-profiles`.
- PR: https://github.com/blockedby/hermes-agent/pull/25
- Worktree: `/home/kcnc/code/hermes/hermes-agent/.worktrees/telegram-business-dialog-profiles`
- Branch: `feat/telegram-business-dialog-profiles`
- Final local state: clean, branch ahead of origin by 7 commits.

## Spec compliance
- Three participant prompt: done. `SessionSource.business_context` and Business prompt block now frames Business dialogs as owner/operator, customer/contact, and Hermes assistant.
- DB-backed settings injection: done. Runtime attaches current profile from `TelegramBusinessDialogProfileStore`; prompt includes `assistant_display_name`, `assistant_prefix`, `dialog_prompt`, and `dialog_notes` for the matching dialog.
- Matching-dialog isolation: done. Tests prove chat A includes only chat A profile and excludes chat B profile/settings.
- Customer text safety: done. Prompt wording says customer slash/control text is not Hermes command input; tests assert customer prompt-injection text is not copied into system prompt.
- Owner manual outgoing context: done. Prompt states owner manual outgoing messages are authoritative conversation context, not current customer requests.
- Old owner-impersonation language: adjusted. Tests assert old “do not speak as Hermes” language is absent from new Business prompt mode.

## Changed files
- `gateway/session.py`
- `gateway/run.py`
- `gateway/platforms/telegram.py`
- `tests/gateway/test_session.py`
- `tests/gateway/test_telegram_business.py`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/plan.md`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task3-prompt-runtime.md`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task3-prompt-runtime.md`
- `progress.md`

## Commits
- `7c6a71812 feat(telegram-business): add dialog profile prompt context`
- `f9323ff73 docs: report business prompt runtime implementation`
- `16bb16878 docs: update business prompt runtime evidence`
- `aeb22a370 docs: update business prompt runtime progress`

## Verification run
- PASS: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_session.py tests/gateway/test_telegram_business.py -- -q -k 'telegram_business_prompt or business_runtime_attaches_matching_database_profile_only or business_profile_change_affects_only_matching_dialog_prompt_signature'`
  - Evidence: 2 files, 4 tests passed.
- PASS (implementer): same targeted container command — 4 tests passed.
- PASS (implementer): `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_session.py tests/gateway/test_telegram_business.py`
  - Evidence: 175 tests passed.
- PASS (implementer): `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m py_compile gateway/session.py gateway/run.py gateway/platforms/telegram.py`.
- BLOCKED before pytest (implementer): `scripts/run_tests_docker.sh ...` failed twice during Docker image rebuild because PyPI/uv downloads reset/EOFed. Existing `hermes-agent:test-runner` container fallback was used. No host pytest/npm/uv was run.

## Issues
- R-01: Prompt/runtime profile foundation implemented and verified with container tests.
- No unresolved current-goal blockers.
- Non-blocking: canonical Docker rebuild path should be retried when PyPI connectivity is stable; not a code/test failure.

## Verdict
- Status: success for delegated slice scope.
- Goal state: achieved for Task 3 plus relevant Task 9 prompt/runtime foundation.
- System readiness: ready for parent integration within the broader PR; remaining plan tasks outside this slice still pending.
