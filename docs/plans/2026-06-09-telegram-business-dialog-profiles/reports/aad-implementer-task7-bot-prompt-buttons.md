PI_RESULT: PASS
TASK: Task 7 — Telegram bot inline buttons for prompt/settings
TASK_PACKAGE: docs/plans/2026-06-09-telegram-business-dialog-profiles
REPORT_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task7-bot-prompt-buttons.md
PROGRESS_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task7-bot-prompt-buttons.md
COMMITS:
- e4acd6ab3: feat(telegram-business): add bot prompt controls
FILES_CHANGED:
- gateway/platforms/telegram.py: added Business prompt keyboard controls, authorized pending prompt edit flow, clear prompt callback, DB profile writes, settings_changed history, and prompt cancel handling before normal owner message dispatch.
- gateway/platforms/telegram_business_history.py: allowed normalized settings_changed history events to retain `fields` list metadata.
- tests/gateway/test_telegram_business.py: added focused Task 7 TDD coverage for keyboard buttons, prompt save, `/cancel`, clear prompt, unauthorized callback rejection, and Add rule regression.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task7-bot-prompt-buttons.md: implementation progress/evidence.
- progress.md: appended Task 7 progress below pre-existing unrelated Task 8 content as explicitly requested; not planned for Task 7 commit because it also contains unrelated dirty Task 8 changes.
AC_VERIFICATION:
- Business card keyboard includes prompt edit and clear prompt buttons: `test_business_mode_keyboard_contains_prompt_controls` in focused container run — passed.
- Prompt callback is owner/admin-authorized only: existing `bm:` auth gate reused; `test_business_prompt_callback_rejects_unauthorized_user_without_pending_prompt` — passed.
- Next owner text is consumed and saved to DB as dialog prompt: `test_business_prompt_button_stores_next_owner_text_as_dialog_prompt` verifies pending state drains, DB `dialog_prompt` is saved, no normal text batch is enqueued, and `settings_changed` history is recorded — passed.
- `/cancel` cancels without saving: `test_business_prompt_cancel_does_not_save_dialog_prompt` exercises command routing through `_handle_command` and verifies existing DB prompt/history are unchanged — passed.
- Clear prompt writes empty prompt to DB: `test_business_clear_prompt_button_writes_empty_prompt_and_history` verifies DB prompt becomes empty and `settings_changed` history is recorded — passed.
- Existing Add rule flow still works: `test_business_add_rule_button_stores_next_owner_text_as_notify_rule` included in focused run — passed.
TESTS_RUN:
- RED expected failure: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q -k 'business_mode_keyboard_contains_prompt_controls or business_prompt_button_stores_next_owner_text_as_dialog_prompt or business_prompt_cancel_does_not_save_dialog_prompt or business_clear_prompt_button_writes_empty_prompt_and_history or business_prompt_callback_rejects_unauthorized_user_without_pending_prompt or business_add_rule_button_stores_next_owner_text_as_notify_rule'` — failed as expected before production changes: missing prompt buttons/pending state/clear behavior; unauthorized callback and Add rule regression passed.
- Focused GREEN: same container command — passed, 6 tests.
- Broader targeted container: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv -e HERMES_TEST_WORKERS=4 -e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 hermes-agent:test-runner scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_business_profiles.py -- -q` — passed, 3 files / 136 tests.
QUALITY_CHECKS:
- Container compile: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv hermes-agent:test-runner /opt/hermes-test-venv/bin/python -m py_compile gateway/platforms/telegram.py gateway/platforms/telegram_business_history.py tests/gateway/test_telegram_business.py` — passed.
- Container lint/static: `docker run --rm -v "$PWD":/workspace -w /workspace -e HERMES_TEST_VENV=/opt/hermes-test-venv hermes-agent:test-runner bash -lc 'if [ -x /opt/hermes-test-venv/bin/ruff ]; then /opt/hermes-test-venv/bin/ruff check gateway/platforms/telegram.py gateway/platforms/telegram_business_history.py tests/gateway/test_telegram_business.py; else echo "ruff not available in /opt/hermes-test-venv"; fi'` — passed (`All checks passed!`).
QUALITY_NOTES:
- Readability/reuse: reused existing Business `bm:` callback auth gate, Add rule pending key shape, chat registry token lookup, DB profile store, card text/keyboard helpers, and history helper; no new abstraction added.
- Error handling/logging: preserved existing best-effort callback edit pattern and user-facing not-found/save-error messages; did not add noisy logs.
- Backend/API/data: prompt save/clear uses `TelegramBusinessDialogProfileStore.upsert_for_chat_entry` so DB remains settings source of truth; history `fields` metadata now survives normalization for `settings_changed` events.
- Frontend/UI: not relevant; no dashboard UI changes.
- DevOps/runtime: no env/config/deployment/runtime wiring changes.
- Security: prompt/clear callbacks remain behind `_is_callback_user_authorized`; no secrets/PII logging added; prompt text is validated by existing profile store bounds/control-char cleanup.
- Concurrency/idempotency: pending prompt token is keyed by owner/chat/thread like existing rule flow and popped once before processing to avoid duplicate saves on retry; clear is idempotent DB write to empty prompt.
- Compatibility/performance: existing mode/draft/add-rule callbacks remain unchanged except for an appended keyboard row; no new network calls or unbounded loops.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: root `progress.md` had pre-existing unrelated Task 8 dirty content before this implementation; preserved and appended as instructed, but left out of Task 7 commit to avoid committing unrelated work.
PARENT_ACTION_REQUIRED:
- Action: none.
- Reason: all delegated implementation and container-only verification completed locally.
- Expected evidence: n/a.
- Safety bounds: n/a.
NOTES: Used existing `hermes-agent:test-runner` container image as requested for container-only checks; no host pytest/npm/uv/build commands were run.
