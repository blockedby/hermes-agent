## Task
- Mission: Resolve root integration follow-up risks for Telegram Business owner context before finalization.
- Target: Business observed-context replay path and Business message classifier.
- Boundaries: Minimal focused fix; no broad Telegram/session/dashboard refactors; no push.
- Done when: owner observed rows are withheld from replayable history and prepended to current customer message; Business classification is unconditional with `sender_business_bot` authoritative.

## Context
- Slice: Telegram Business owner/manual outgoing context follow-up.
- Task package: `docs/plans/2026-06-09-telegram-business-owner-context`
- Report path: `docs/plans/2026-06-09-telegram-business-owner-context/reports/slice-owner-followup.md`
- Worktree: `/home/kcnc/code/hermes/hermes-agent/.worktrees/t_42400-telegram-business-owner-context`
- Branch: `pi/t_42400-telegram-business-owner-context`
- Ownership model: stayed whole. Attempted `aad-implementer` delegation, but nested subagent depth was blocked (`depth=2, max=2`), so the slice owner implemented directly.

## Changed files
- `gateway/run.py`
- `gateway/platforms/telegram.py`
- `tests/gateway/test_telegram_business.py`
- `tests/gateway/test_telegram_group_gating.py`
- `docs/plans/2026-06-09-telegram-business-owner-context/plan.md`
- `docs/plans/2026-06-09-telegram-business-owner-context/verification/followup-local.md`

## Spec compliance
- Business observed owner context withheld from replayable `conversation_history`: done. The run path now combines `event.channel_prompt` with generated `context_prompt` before `_build_gateway_agent_history()` decides whether to separate observed rows.
- Business observed owner context prepended to current customer message without hiding current turn behind history offsets: done and tested in `test_observed_business_owner_context_uses_session_prompt_marker_not_event_prompt`.
- Unconditional three-way Business classification: done. `_is_business_self_message()` no longer returns false solely because `business_ignore_self_messages` is disabled.
- `sender_business_bot` authoritative for `bot_outgoing`: preserved; classifier still checks it before owner identity.

## Acceptance verification
- AC1: Business observed owner rows are omitted from replayable history when the marker comes from `build_session_context_prompt()`.
  - Covered by: `tests/gateway/test_telegram_group_gating.py::test_observed_business_owner_context_uses_session_prompt_marker_not_event_prompt`
  - Result: passed.
- AC2: Observed owner context is prepended to the current customer message and the current user turn remains visible after repair/history-offset logic.
  - Covered by: same test.
  - Result: passed.
- AC3: Owner/manual outgoing classifies as `owner_manual_outgoing` even with legacy self-ignore disabled.
  - Covered by: `test_business_classifier_owner_identity_ignores_legacy_self_ignore_gate` and `test_business_update_treats_owner_self_message_as_context_when_flag_disabled`.
  - Result: passed.
- AC4: `sender_business_bot` remains authoritative for `bot_outgoing`.
  - Covered by: `test_business_classifier_uses_sender_business_bot_for_bot_outgoing` and exact-class tests.
  - Result: passed.

## Verification run
- Local / targeted checks:
  - `HERMES_TEST_VENV=/home/kcnc/code/hermes/hermes-agent/venv scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_group_gating.py tests/gateway/test_session.py -- -q`: passed, 204 tests.
  - Evidence artifact: `docs/plans/2026-06-09-telegram-business-owner-context/verification/followup-local.md`.
- Remote checks / CI: not available; no push requested.

## Issues
### Issue R-01: Business observed owner rows were replayable when only session context had the marker
- Evidence: `_build_gateway_agent_history(history, channel_prompt=...)` received only `event.channel_prompt`; Telegram Business marker lived in generated `context_prompt`.
- Resolution: pass a combined detection prompt (`channel_prompt` + `context_prompt`) and make marker matching case-insensitive.

### Issue R-02: Owner/manual classification depended on legacy self-ignore gate
- Evidence: `_is_business_self_message()` returned `False` when `_business_ignore_self_messages_enabled()` was false.
- Resolution: remove that short-circuit for Business classification; owner identity now classifies as `owner_manual_outgoing` regardless of the legacy gate, while `sender_business_bot` still wins first.

## System readiness
- Routes / registration: unchanged.
- Services / APIs: unchanged.
- Config / env / secrets: unchanged; legacy flag no longer suppresses Business owner/manual classification.
- Database / migrations: unchanged.
- Runtime / deployment wiring: unchanged.

## Verdict
- Status: success.
- Goal state: fully achieved for the follow-up risks.
- Final readiness: ready for root finalization after any parent-level branch prep.
- Blockers: none.
