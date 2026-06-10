## Task
- Mission: Implement Task 6 from `docs/plans/2026-06-09-telegram-business-dialog-profiles/plan.md`: explicit safe invocation policy for Telegram Business.
- Target: Telegram Business ingress/routing for configured bot mentions and DB `invocation_policy`.
- Boundaries: Kept scope to invocation routing. Did not implement bot prompt buttons, dashboard UI, or broader Task 10 permission/history cleanup.
- Ownership model: Slice stayed whole; implementation delegated to one `aad-implementer` task and owner performed fresh container verification.

## Context
- Worktree: `/tmp/pi-worktree-78ff96c3-0`
- Branch: `pi-parallel-78ff96c3-0`
- Task package: `docs/plans/2026-06-09-telegram-business-dialog-profiles`
- Implementer report: `docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task6-invocation-policy.md`
- Verification artifact: `docs/plans/2026-06-09-telegram-business-dialog-profiles/verification/task6-invocation-policy.md`

## Changed files
- `gateway/platforms/telegram.py`
- `gateway/platforms/base.py`
- `gateway/run.py`
- `tests/gateway/test_telegram_business.py`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task6-invocation-policy.md`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/verification/task6-invocation-policy.md`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task6-invocation-policy.md`

## Spec compliance
- DB invocation policy `off|mention_draft|mention_direct`: done; Telegram Business routing reads profile policy and applies it per event.
- Configured bot username mention detection: done; case-insensitive configured username match, punctuation/newline handled; no unknown-username fallback.
- `mention_draft`: done; queues approval-safe draft from watch/non-draft modes without persisting mode.
- `mention_direct`: done; one-shot direct behavior through `business_mode=auto` metadata when reply is allowed, without persisting chat mode.
- Slash commands remain blocked: done; slash-like Business customer messages, including `/restart@BotName`, stay blocked before command dispatch.
- Preserve normal mode behavior: done; broader existing Business test file remains green.

## Acceptance verification
- Owner fresh targeted container run:
  - Command: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q -k 'mention or invocation or slash'`
  - Result: passed, 17 tests.
- Owner fresh broader touched-file container run:
  - Command: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q`
  - Result: passed, 107 tests.
- Owner fresh compile check:
  - Command: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m py_compile gateway/platforms/telegram.py gateway/platforms/base.py gateway/run.py tests/gateway/test_telegram_business.py`
  - Result: passed.
- Owner fresh lint check:
  - Command: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m ruff check gateway/platforms/telegram.py gateway/platforms/base.py gateway/run.py tests/gateway/test_telegram_business.py`
  - Result: passed (`All checks passed!`).

## Commits
- `b22ec789b` — `feat(telegram-business): add mention invocation policy`
- `222284502` — `docs: add task6 invocation policy report`
- `921c078df` — `docs: update task6 invocation report commits`

## Issues
- Blocking: none.
- Follow-up: none created for this slice. Task 10 remains the planned scope to further define can-reply-false visibility/history for direct-send failure behavior.
- Unresolved current-goal issues: none.

## Verdict
- Status: success.
- Final slice done-state: Task 6 implemented, committed, and verified with container-only checks.
- System readiness: ready for parent integration/PR continuation within the existing Telegram Business dialog profiles branch.
