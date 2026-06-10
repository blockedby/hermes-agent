## Task
- Mission: Implement Task 7 bot inline prompt edit/clear controls for Telegram Business dialog profiles.
- Target: `gateway/platforms/telegram.py`, Business history normalization, and Telegram Business tests.
- Boundaries: Bot-button prompt edit/clear only; no dashboard UI or mention invocation changes; container-only verification.

## Context
- Task package: `docs/plans/2026-06-09-telegram-business-dialog-profiles`
- Worktree: `/home/kcnc/code/hermes/hermes-agent/.worktrees/telegram-business-dialog-profiles`
- PR: https://github.com/blockedby/hermes-agent/pull/25
- Implementation model: slice stayed whole; implementation delegated to one `aad-implementer`.

## Spec compliance
- `🧠 Prompt` and `🧹 Clear prompt` added to Business owner cards: done, tested.
- Authorized `bm:p:<token>` pending prompt flow modeled after Add rule: done, tested.
- Next owner text saves `dialog_prompt` via DB profile store: done, tested.
- `/cancel` cancels without save: done, tested.
- Clear prompt writes empty prompt: done, tested.
- `settings_changed` history recorded: done, tested.
- Dashboard UI / mention invocation: not touched by design.

## Acceptance verification
- Fresh owner container verification passed:
  `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_business_profiles.py -- -q`
  Result: 3 files / 136 tests passed.
- Implementer also recorded RED-before-GREEN focused tests, focused GREEN (6 tests), container `py_compile`, and container `ruff check` in `reports/aad-implementer-task7-bot-prompt-buttons.md`.

## Changed files
- `gateway/platforms/telegram.py`
- `gateway/platforms/telegram_business_history.py`
- `tests/gateway/test_telegram_business.py`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task7-bot-prompt-buttons.md`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task7-bot-prompt-buttons.md`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/slice-owner-task7.md`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/plan.md`
- `progress.md` appended with Task 7 progress but left uncommitted because it already contained unrelated Task 8 progress.

## Commits
- `e4acd6ab3 feat(telegram-business): add bot prompt controls`
- `2198f9ae7 docs: report task7 bot prompt controls`
- `b01e629b2 docs: record task7 slice owner evidence`

## Issues
- Blocking: none.
- Follow-ups: none created for Task 7.
- Note: root `progress.md` contains unrelated pre-existing Task 8 content; preserved and not committed by Task 7.

## Verdict
- Status: success.
- Goal state: achieved for Task 7.
- System readiness: ready within targeted container-tested scope.
