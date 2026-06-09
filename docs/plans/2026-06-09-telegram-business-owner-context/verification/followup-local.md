# Follow-up local verification

Date: 2026-06-09
Worktree: `/home/kcnc/code/hermes/hermes-agent/.worktrees/t_42400-telegram-business-owner-context`
Branch: `pi/t_42400-telegram-business-owner-context`

## Command

```bash
HERMES_TEST_VENV=/home/kcnc/code/hermes/hermes-agent/venv scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_group_gating.py tests/gateway/test_session.py -- -q
```

## Result

Passed.

Excerpt:

```text
✓ tests/gateway/test_session.py (79✓, 1.5s)
✓ tests/gateway/test_telegram_group_gating.py (45✓, 1.7s)
✓ tests/gateway/test_telegram_business.py (80✓, 2.0s)

=== Summary: 3 files, 204 tests passed, 0 failed (0% complete) in 2.0s (32 workers) ===
```

## Acceptance mapping

- Business observed owner rows are withheld from replayable `conversation_history` when the Telegram Business marker comes from generated `build_session_context_prompt()` evidence: `test_observed_business_owner_context_uses_session_prompt_marker_not_event_prompt` passed.
- Observed owner context is prepended to the current customer message and the current user turn remains visible after history repair/history-offset slicing evidence: same test passed.
- Business classification is unconditional for owner/manual outgoing even when `_business_ignore_self_messages` is disabled evidence: `test_business_classifier_owner_identity_ignores_legacy_self_ignore_gate` and `test_business_update_treats_owner_self_message_as_context_when_flag_disabled` passed.
- `sender_business_bot` remains authoritative for `bot_outgoing` evidence: existing and adjusted Business classifier tests passed.
