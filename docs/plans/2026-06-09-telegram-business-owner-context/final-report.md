## Task
- Mission: Implement Telegram Business owner/manual outgoing context and `sender_business_bot` classifier behavior for issue #42400.
- Target: Telegram Business update handling, Business history/context metadata, observed transcript replay, and targeted tests.
- Boundaries: No unrelated Telegram/session/dashboard refactors; no dependency/config changes; no push.
- Done when: bot outgoing, owner/manual outgoing, and customer inbound are separated; owner/manual messages become context/history only; dashboard latest customer message contract remains intact; targeted suites pass.
- Expected evidence: slice reports and fresh root `scripts/run_tests.sh` verification.

## Context
- Thread: User requested AAD-owned non-trivial implementation.
- Slice: Single coherent slice, because classifier + owner context + dashboard/latest verification share one Telegram Business behavior boundary.
- Task package: `docs/plans/2026-06-09-telegram-business-owner-context`
- Reports: `reports/slice-owner.md`, `reports/slice-owner-followup.md`
- Verification: `verification/local.md`, `verification/followup-local.md`, `verification/root-final.md`
- Worktree: `/home/kcnc/code/hermes/hermes-agent/.worktrees/t_42400-telegram-business-owner-context`
- Branch: `pi/t_42400-telegram-business-owner-context`

## Spec compliance
- Classify Business messages as `bot_outgoing`, `owner_manual_outgoing`, `customer_inbound`: done; `_classify_business_message()` added and tested.
- `sender_business_bot` authoritative for bot outgoing: done; checked before owner/self identity.
- `bot_outgoing` ignored/deduped: done; no enqueue/history duplicate.
- `owner_manual_outgoing` context/history only: done; records `owner_outbound` history and observed transcript when session store exists; no enqueue/watch/draft/auto and no registry latest-customer overwrite.
- `customer_inbound` existing behavior: preserved by regression suites.
- Dashboard latest-message contract: preserved by registry assertions and dashboard API tests.
- Context-only observed transcript: done via existing observed-context separation path, using generated Telegram Business session prompt marker in addition to event channel prompt.

## Acceptance verification
- AC1 classifier classes:
  - Covered by: `test_business_classifier_has_exact_behavior_classes`.
  - Result: passed.
- AC2 bot outgoing ignored/deduped:
  - Covered by: `test_business_classifier_uses_sender_business_bot_for_bot_outgoing`.
  - Result: passed.
- AC3 owner/manual outgoing history/context-only/no latest overwrite:
  - Covered by: `test_business_owner_manual_outgoing_records_history_only_and_preserves_latest_customer`.
  - Result: passed.
- AC4 customer inbound preserved:
  - Covered by: final targeted Business/dashboard/group/session suites.
  - Result: passed.
- AC5 observed owner context is future-turn context, not replayable user history:
  - Covered by: `test_observed_business_owner_context_uses_session_prompt_marker_not_event_prompt`.
  - Result: passed.
- AC6 dashboard latest draft source stays last customer inbound:
  - Covered by: owner outbound registry preservation assertion and `test_telegram_business_dashboard_api.py`.
  - Result: passed.

## System readiness
- Routes / registration: unchanged.
- Services / APIs: dashboard API behavior preserved.
- Config / env / secrets: unchanged; legacy self-ignore flag no longer suppresses Business owner/manual classification.
- Permissions / access: unchanged.
- Database / migrations: no schema migration; existing SessionDB `observed` support reused.
- Frontend-backend integration: dashboard contract tested at API/service layer.
- Runtime / deployment wiring: unchanged.

## Verification run
- Local / targeted checks:
  - `HERMES_TEST_VENV=/home/kcnc/code/hermes/hermes-agent/venv scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_group_gating.py tests/gateway/test_session.py -- -q`: passed, 219 tests.
  - Evidence: `verification/root-final.md`.
- Local / full checks:
  - Not run; targeted gateway suites directly cover the changed Telegram Business/session/dashboard paths.
- Remote checks / CI:
  - Not available before push.

## Issues
### Issue R-01: Bot and owner/manual Business outgoing messages were collapsed as self messages
- Description: `_is_business_self_message()` caused both bot echoes and manual owner outgoing messages to be ignored before context/history handling.
- Evidence: prior `_handle_business_update()` self branch.
- Resolution: added three-way classifier and separate behavior branches.
- Depends on: none.

### Issue R-02: Owner/manual context initially risked replaying as ordinary history
- Description: observed owner rows needed the generated Business session prompt marker to participate in observed-context separation.
- Evidence: follow-up integration review of `_build_gateway_agent_history(channel_prompt=...)` call path.
- Resolution: run path now combines event channel prompt and generated context prompt for observed-context detection; test added.
- Depends on: none.

## Side findings
- Blocking findings folded into active work: R-01, R-02.
- Non-blocking findings tracked separately: none.

## Verdict
- Status: success.
- Goal state: fully achieved.
- Final readiness: ready for review/push if desired.
- Summary: Telegram Business update handling now separates bot outgoing, owner/manual outgoing, and customer inbound with tested context/history and dashboard latest-message safeguards.
