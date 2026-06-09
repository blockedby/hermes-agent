# Local verification

Date: 2026-06-09
Worktree: `/home/kcnc/code/hermes/hermes-agent/.worktrees/t_42400-telegram-business-owner-context`
Branch: `pi/t_42400-telegram-business-owner-context`

## Environment note
- The worktree itself has no `.venv`/`venv`; per `scripts/run_tests.sh` support, used `HERMES_TEST_VENV=/home/kcnc/code/hermes/hermes-agent/venv`.
- An attempted run with `/home/kcnc/code/hermes/hermes-agent/.venv` failed because that venv lacks pytest; not product-related.

## Commands

### Targeted Business suite
Command:
```bash
HERMES_TEST_VENV=/home/kcnc/code/hermes/hermes-agent/venv scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q
```
Result: passed.
Evidence summary:
```text
✓ tests/gateway/test_telegram_business.py (79✓, 1.8s)
Summary: 1 files, 79 tests passed, 0 failed
```

### Acceptance regression set
Command:
```bash
HERMES_TEST_VENV=/home/kcnc/code/hermes/hermes-agent/venv scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_group_gating.py tests/gateway/test_session.py -- -q
```
Result: passed.
Evidence summary:
```text
✓ tests/gateway/test_telegram_business_dashboard_api.py (15✓, 0.7s)
✓ tests/gateway/test_session.py (79✓, 1.4s)
✓ tests/gateway/test_telegram_group_gating.py (44✓, 1.6s)
✓ tests/gateway/test_telegram_business.py (79✓, 1.9s)
Summary: 4 files, 217 tests passed, 0 failed
```

## Acceptance mapping
- AC1 classifier classes: covered by `test_business_classifier_has_exact_behavior_classes` and `test_business_classifier_uses_sender_business_bot_for_bot_outgoing`; passed.
- AC2 bot outgoing no enqueue/no duplicate history: covered by `test_business_classifier_uses_sender_business_bot_for_bot_outgoing`; passed.
- AC3 owner/manual outgoing history/context-only/no side effects: covered by `test_business_owner_manual_outgoing_records_history_only_and_preserves_latest_customer`; passed.
- AC4 customer inbound preserved: covered by existing `test_telegram_business.py` plus dashboard/group/session regression files; passed.
- AC5 dashboard latest-message/draft source preserved: covered by owner outbound registry preservation assertion and `test_telegram_business_dashboard_api.py`; passed.
- AC6 targeted evidence recorded here: done.
