# Telegram Business owner/manual outgoing context plan

## Intake
- Goal: implement Telegram Business classifier and owner/manual outgoing context/history behavior for issue #42400.
- In scope: classify Business updates into `bot_outgoing`, `owner_manual_outgoing`, `customer_inbound`; use `Message.sender_business_bot` as authoritative bot-outgoing indicator; preserve bot echo dedupe; record owner/manual outbound as context/history only; protect registry/dashboard latest customer message; update targeted tests.
- Out of scope: broad Telegram/session/dashboard refactors, dependency/config changes, unrelated approval flows.
- Done state: targeted suites pass via `scripts/run_tests.sh`; verification recorded in `verification/local.md`; owner report in `reports/slice-owner.md`.
- Blocking unknowns: exact Telegram SDK object shape in tests is mocked; implement against attribute access only.

## Repo orientation
- Main Business update path: `gateway/platforms/telegram.py::_handle_business_update`.
- Existing self/owner echo logic: `_is_business_self_message`; currently conflates bot and owner and ignores both entirely.
- Registry latest customer data: `telegram_business_chats.py::upsert_from_message`; do not call for owner outbound.
- History store: `gateway/platforms/telegram_business_history.py`; event allowlist and normalized metadata fields live here.
- Observed context pattern: `gateway/run.py::_build_gateway_agent_history` separates rows marked `observed` when channel prompt contains observed marker; `gateway/session.py` adds Telegram Business platform notes.
- Target tests: `tests/gateway/test_telegram_business.py`, `tests/gateway/test_telegram_business_dashboard_api.py`, `tests/gateway/test_telegram_group_gating.py`; add `tests/gateway/test_session.py` only if session/run prompt prep changes.

## Reuse discovery
- Reuse `TelegramBusinessHistoryStore.append_event` through adapter `_record_business_history_event`.
- Reuse Business key helpers: `_business_connection_id_from_message`, `_direct_messages_topic_id_from_message`, `_telegram_message_chat_id`, `_business_thread_id`.
- Reuse observed transcript invariant rather than adding a new history replay path; if implemented, ensure observed owner context is not replayed as current customer request.
- Reuse dashboard tests checking `source=latest` from registry latest fields.

## Missing pieces
- A small classifier helper returning exactly `bot_outgoing`, `owner_manual_outgoing`, or `customer_inbound`.
- History allowlist/type support for `owner_outbound` and safe metadata fields such as actor name/classification/delivery/source.
- Owner/manual outbound path: record history/context only and stop; no enqueue/notifications/mode rules/registry upsert.
- Tests for bot outgoing via `sender_business_bot`, owner manual outbound, registry/latest-message preservation, and classifier classes.

## Plan tasks

### Task 1: Business classifier and bot outgoing protection
Goal: add explicit classifier with the three accepted behavior classes and use `sender_business_bot` to identify bot outgoing.
Boundary: Telegram adapter Business update path.
Existing pattern / reuse: existing `_is_business_self_message` and Business helper methods.
Missing change: helper and `_handle_business_update` branch.
Scope / likely files: `gateway/platforms/telegram.py`, `tests/gateway/test_telegram_business.py`.
Acceptance criteria:
- Classifier returns only `bot_outgoing`, `owner_manual_outgoing`, `customer_inbound`.
- `sender_business_bot` truthy means `bot_outgoing` even if other sender fields resemble owner/customer.
- Bot outgoing does not enqueue or create Business history duplicate.
Test plan: targeted unit tests in `test_telegram_business.py`; run relevant suite.
Dependencies: none.
Executor: `aad-implementer`.
Report: `reports/aad-implementer-business-classifier.md`.

### Task 2: Owner/manual outbound history and context-only handling
Goal: owner/manual outgoing Business messages record safe history/context only and never trigger agent/watch/draft/auto/latest-customer updates.
Boundary: Telegram adapter Business history/session context integration.
Existing pattern / reuse: `_record_business_history_event`; observed context pattern in `gateway/run.py` if session context hook is practical.
Missing change: add `owner_outbound` event type, safe metadata normalization, and context-only observed transcript write if the adapter has a session store path available; avoid registry `upsert_from_message`.
Scope / likely files: `gateway/platforms/telegram.py`, `gateway/platforms/telegram_business_history.py`, maybe `gateway/run.py`/`gateway/session.py` only if needed for observed-context marker.
Acceptance criteria:
- `owner_manual_outgoing` creates `owner_outbound` history with safe metadata.
- No enqueue, owner notification, draft/auto trigger, or registry latest customer overwrite.
- If session store exists, future LLM turns can see owner outbound as observed context, not current customer request.
Test plan: targeted tests in `test_telegram_business.py`; add `test_session.py` only if session/run prompt behavior changes.
Dependencies: Task 1 classifier.
Executor: `aad-implementer`.
Report: `reports/aad-implementer-owner-outbound.md`.

### Task 3: Dashboard latest-message contract and verification
Goal: prove dashboard latest/draft source remains last customer inbound after owner outbound.
Boundary: dashboard API + registry/history interaction tests.
Existing pattern / reuse: `tests/gateway/test_telegram_business_dashboard_api.py` latest draft tests and registry entry setup.
Acceptance criteria:
- Dashboard `source=latest` still uses last customer inbound after owner outbound.
- Target suites pass through `scripts/run_tests.sh`.
Test plan: `scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_group_gating.py -q` plus session tests if changed.
Dependencies: Tasks 1-2.
Executor: `aad-implementer` or owner final verification.
Report: `verification/local.md`.

## Dependency graph
- Task 1 blocks Task 2; Task 3 waits on implementation.
- Slice stays whole; no sub-slices needed.

## Execution ledger
- 2026-06-09 owner: created plan from routing context and repo orientation. Ready to dispatch implementer for Tasks 1-3 as a single coherent implementation task.

## Implementation update
- 2026-06-09 owner: Nested subagent dispatch was blocked by subagent depth (`depth=2, max=2`), so the slice owner implemented directly within the delegated worktree.
- Changed files:
  - `gateway/platforms/telegram.py`
  - `gateway/platforms/telegram_business_history.py`
  - `gateway/run.py`
  - `gateway/session.py`
  - `tests/gateway/test_telegram_business.py`
- Task 1 status: done. Added `_classify_business_message()` returning exactly `bot_outgoing`, `owner_manual_outgoing`, `customer_inbound`; `sender_business_bot` is authoritative for bot outgoing.
- Task 2 status: done. Owner/manual outgoing records `owner_outbound` history with safe metadata and, when `_session_store` exists, appends observed context-only transcript. It does not enqueue, notify, trigger modes, or update registry latest customer fields.
- Task 3 status: done. Targeted regression suite passed; evidence in `verification/local.md`.

## Follow-up integration fix
- 2026-06-09 owner: Root integration found two acceptance risks: Business observed owner rows were not withheld when only the generated session context prompt contained the marker, and owner/manual Business classification still depended on the legacy `business_ignore_self_messages` gate.
- Delegation: attempted `aad-implementer` dispatch for the follow-up, but nested subagent depth remained blocked (`depth=2, max=2`), so the slice owner implemented directly in the delegated worktree.
- Changed files:
  - `gateway/run.py`
  - `gateway/platforms/telegram.py`
  - `tests/gateway/test_telegram_business.py`
  - `tests/gateway/test_telegram_group_gating.py`
  - `docs/plans/2026-06-09-telegram-business-owner-context/verification/followup-local.md`
  - `docs/plans/2026-06-09-telegram-business-owner-context/reports/slice-owner-followup.md`
- Fixes:
  - `_build_gateway_agent_history()` now receives a combined observed-context detection prompt built from both `event.channel_prompt` and generated `context_prompt`, so Telegram Business observed owner rows are withheld even when the marker comes from `build_session_context_prompt()`.
  - Observed-context marker detection is case-insensitive to match the generated Telegram Business prompt text.
  - `_is_business_self_message()` no longer short-circuits on `business_ignore_self_messages`; the three-way Business classifier remains unconditional, with `sender_business_bot` checked first and owner identity still producing `owner_manual_outgoing`.
- Follow-up verification: `HERMES_TEST_VENV=/home/kcnc/code/hermes/hermes-agent/venv scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_group_gating.py tests/gateway/test_session.py -- -q` passed, 204 tests. Evidence: `verification/followup-local.md`.

## Final done-state
- Spec compliance: original acceptance criteria and root follow-up risks are satisfied by targeted tests.
- Open blockers: none.
- Follow-up candidates: none identified.
