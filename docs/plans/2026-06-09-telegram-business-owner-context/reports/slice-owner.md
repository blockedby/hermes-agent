## Task
- Mission: Implement Telegram Business owner/manual outgoing context + `sender_business_bot` classifier behavior for issue #42400.
- Target: Telegram Business update path, Business history normalization, observed-context prompt handling, and targeted tests.
- Boundaries: No unrelated Telegram/session/dashboard refactors, no dependency/config changes, no push.
- Done when: three-way classifier exists, bot echoes are ignored/deduped, owner/manual outgoing is history/context-only, dashboard latest customer message is preserved, targeted suites pass.
- Expected evidence: `scripts/run_tests.sh` targeted gateway/session suites and verification artifact.

## Context
- Slice: Telegram Business classifier + owner outbound behavior.
- Task package: `docs/plans/2026-06-09-telegram-business-owner-context`
- Report path: `docs/plans/2026-06-09-telegram-business-owner-context/reports/slice-owner.md`
- Worktree: `/home/kcnc/code/hermes/hermes-agent/.worktrees/t_42400-telegram-business-owner-context`
- Branch: `pi/t_42400-telegram-business-owner-context`
- Ownership model: stayed whole. Attempted `aad-implementer` delegation, but nested subagent depth blocked dispatch, so slice owner implemented directly.
- Commit: changes committed on current branch with message `feat: classify telegram business owner outbound`; use `git log -1 --oneline` for final hash.

## Changed files
- `gateway/platforms/telegram.py`
- `gateway/platforms/telegram_business_history.py`
- `gateway/run.py`
- `gateway/session.py`
- `tests/gateway/test_telegram_business.py`
- Task package files under `docs/plans/2026-06-09-telegram-business-owner-context/`

## Spec compliance
- Classifier with exactly `bot_outgoing`, `owner_manual_outgoing`, `customer_inbound`: done; `_classify_business_message()` added and tested.
- `sender_business_bot` authoritative for bot outgoing: done; checked before owner/self fallback.
- Bot outgoing no enqueue/no duplicate history: done; bot branch logs and returns without registry/history/enqueue.
- Owner/manual outgoing history/context only: done; records `owner_outbound`, appends observed transcript when `_session_store` exists, and bypasses enqueue/notifications/modes/registry upsert.
- Customer inbound behavior preserved: done; existing Business tests and regressions pass.
- Dashboard latest-message contract: done; owner outbound test asserts registry latest customer fields remain unchanged and dashboard API suite passes.

## Acceptance verification
- AC1: Business classifier returns/uses exactly three behavior classes.
  - Covered by: `test_business_classifier_has_exact_behavior_classes`.
  - Result: passed.
- AC2: `bot_outgoing` has no enqueue/history duplicate; self echo protection preserved.
  - Covered by: `test_business_classifier_uses_sender_business_bot_for_bot_outgoing` and existing self/Business tests.
  - Result: passed.
- AC3: `owner_manual_outgoing` records `owner_outbound`, observed context if session store exists, no enqueue/notification/draft/auto/latest overwrite.
  - Covered by: `test_business_owner_manual_outgoing_records_history_only_and_preserves_latest_customer`.
  - Result: passed.
- AC4: `customer_inbound` behavior preserved.
  - Covered by: existing `tests/gateway/test_telegram_business.py` and regression files.
  - Result: passed.
- AC5: Dashboard latest-message/draft source remains last customer inbound after owner outbound.
  - Covered by: registry preservation assertion plus `tests/gateway/test_telegram_business_dashboard_api.py`.
  - Result: passed.
- AC6: Targeted test evidence recorded.
  - Covered by: `verification/local.md`.
  - Result: done.

## Verification run
- Local / targeted checks:
  - `HERMES_TEST_VENV=/home/kcnc/code/hermes/hermes-agent/venv scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q`: passed, 79 tests.
  - `HERMES_TEST_VENV=/home/kcnc/code/hermes/hermes-agent/venv scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_group_gating.py tests/gateway/test_session.py -- -q`: passed, 217 tests.
- Artifact: `docs/plans/2026-06-09-telegram-business-owner-context/verification/local.md`.
- Environment note: worktree had no local venv; used main checkout venv via `HERMES_TEST_VENV`. An attempted `.venv` run failed because that venv lacks pytest, classified as environment-only.
- Remote checks / CI: not available; branch not pushed.

## Issues
### Issue R-01: Owner/self Business messages were ignored without preserving manual owner context
- Evidence: previous `_is_business_self_message()` branch ignored both bot and owner/self messages before registry/history/session handling.
- Resolution: split behavior with classifier; owner/manual records `owner_outbound` history and observed transcript only.

### Issue R-02: Bot outgoing needed authoritative `sender_business_bot` classification
- Evidence: issue scope required Telegram `Message.sender_business_bot` as the authoritative bot outgoing signal.
- Resolution: classifier checks `sender_business_bot` first and suppresses bot outgoing before history/enqueue.

## Side findings
- Blocking findings folded into active work: R-01, R-02.
- Non-blocking findings tracked separately: none.
- Follow-up candidates: none identified.

## System readiness
- Routes / registration: unchanged, ready.
- Services / APIs: dashboard API contract preserved by tests.
- Config / env / secrets: unchanged.
- Database / migrations: no schema migration; existing SessionDB observed flag reused.
- Runtime / deployment wiring: unchanged.

## Verdict
- Status: success.
- Goal state: fully achieved for the delegated slice.
- Final readiness: ready for parent integration/PR preparation.
- Summary: Telegram Business updates now distinguish bot outgoing, owner/manual outgoing, and customer inbound; owner manual messages become safe context/history only without disturbing customer inbound dashboard state.

## Next-agent brief
- Objective: integrate/finalize branch if needed.
- Settled already: implementation and targeted verification are complete; do not reopen broad Telegram refactors.
- Boundary: do not push unless parent/root workflow asks.
- Verification target: reuse `verification/local.md`; rerun targeted suite after any integration/rebase.
