## Task
- Mission: Inspect Task 5 surfaces for durable Telegram Business voice media + STT transcript persistence.
- Target: `gateway/platforms/telegram.py`, `gateway/platforms/telegram_business_history.py`, `gateway/run.py`, `tests/gateway/test_stt_config.py`, `tests/gateway/test_telegram_business.py`
- Boundaries: read-only discovery only; do not edit files or broaden scope beyond Business voice/media persistence.
- Done when: owner can implement durable Business voice media records, linked STT transcript records, and matching tests.
- Expected evidence: exact reuse points, missing schema/wiring, and verification options.

## Context
- Task name: Telegram Business media ingestion — Task 5
- Task package: `docs/plans/2026-05-26-telegram-business-media`
- Report path: `docs/plans/2026-05-26-telegram-business-media/reports/explorer.md`
- Worktree: `/home/kcnc/code/hermes/hermes-agent`
- Branch: `epic/telegram-business-media` (`52d93fa27`)
- Verify scope: Task 5 only
- Review target: persistent Business voice media + transcript history/session data

## Spec compliance
- Business voice updates are currently not persisted because `_handle_business_update()` drops any Business message without `text` (`gateway/platforms/telegram.py:6619-6647`).
  - Status: missing
  - Evidence: non-text guard + no media branch in Business handler
- Normal Telegram voice/audio caching + STT enrichment already exist and are reusable.
  - Status: done/reusable
  - Evidence: `_handle_media_message()` caches `voice/audio` (`gateway/platforms/telegram.py:7012-7032`) and `_prepare_inbound_message_text()` routes `MessageType.VOICE` through `_enrich_message_with_transcription()` (`gateway/run.py:7710-7804`)
- Business history store currently preserves only basic string/list fields; it has no structured media/transcript slots.
  - Status: missing
  - Evidence: `_normalize_event()` only whitelists `event_id/message_id/approval_id/mode/actor_user_id/rule_id/rule_label/status/source` plus `message_ids` (`gateway/platforms/telegram_business_history.py:81-158`)
- Session transcript DB already persists the enriched user turn once the event reaches the gateway path.
  - Status: done/reusable
  - Evidence: transcript append happens after `_prepare_inbound_message_text()` in `_process_message_background()` (`gateway/run.py:8770-8888`)
- There is no existing write-back hook that stores STT result/provider/status into Telegram Business history.
  - Status: missing
  - Evidence: `_enrich_message_with_transcription()` returns only enriched text, not a structured persistence payload (`gateway/run.py:14456-14541`)

## Acceptance verification
- AC1: Business voice inbound creates a durable history record with message id, business key, cached audio/media reference, and media kind.
  - Covered by: code inspection
  - Result: missing in current code
  - Evidence: Business handler ignores non-text messages; history store has no media fields.
- AC2: Successful STT creates a durable Business history record linked to the same message/chat key and the session transcript still contains the enriched user turn.
  - Covered by: code inspection
  - Result: partial
  - Evidence: session transcript persistence already exists; business-history write-back does not.
- AC3: Disabled/failed STT records status without pretending there is a transcript.
  - Covered by: code inspection
  - Result: missing
  - Evidence: `_enrich_message_with_transcription()` only embeds failure text into prompt text; no structured status persistence exists.

## System readiness
- Routes / registration: Business update handler exists; no media branch yet for voice persistence.
- Services / APIs: no structured Business transcription persistence API/helper exists.
- Config / env / secrets: STT config already exists and is consumed by gateway STT flow.
- Database / migrations: no DB migration; Business history JSON normalization likely needs extension.
- Frontend-backend integration: dashboard/history can already read Business history JSON; new fields must stay backward-compatible.
- Runtime / deployment wiring: not assessed for this discovery task.

## Issues
### Blocking
- Business voice messages are dropped before media/STT processing because `_handle_business_update()` only accepts text.
- `TelegramBusinessHistoryStore` cannot currently retain structured media/transcript metadata.

### Non-blocking follow-up candidates
- If the fix adds a new structured record, tests should assert both history JSON contents and unchanged session transcript behavior.

## Suggested plan tasks
- Add a Business voice persistence hook in `gateway/platforms/telegram.py` that records inbound voice media metadata before enqueueing.
- Extend `TelegramBusinessHistoryStore._normalize_event()` to preserve safe transcript/media/status fields.
- Add Business-specific tests in `tests/gateway/test_telegram_business.py` plus STT-path coverage in `tests/gateway/test_stt_config.py`.

## Suggested verification
- Targeted:
  - `scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_stt_config.py -q`
- Broader/final:
  - add a focused Business voice/audio regression run once the new tests exist

## Verdict
- Status: partial
- Goal state: not achieved in current code
- Final readiness: not ready
- Summary: the session transcript path is already in place, but Business voice media/transcript durability still needs an explicit adapter/history-store write-back path.

## Next-agent brief
- Objective: implement durable Telegram Business voice media + STT transcript persistence.
- Target: `gateway/platforms/telegram.py`, `gateway/platforms/telegram_business_history.py`, `gateway/run.py`, tests in `tests/gateway/test_telegram_business.py` and `tests/gateway/test_stt_config.py`
- Settled already: session transcript persistence already captures the enriched user turn once the event reaches the gateway path.
- Boundaries: keep changes localized; do not redesign unrelated Business routing or outbound send behavior.
- Verification target: a Business voice message yields a structured history record, a linked transcript/status record, and the existing session transcript still contains the spoken text when STT succeeds.
- Expected output: concise implementation report with tests run and exact evidence.

---

## Task
- Mission: Inspect Tasks 1-4 for shared Telegram media handling and Business media routing.
- Target: `gateway/platforms/telegram.py`, `gateway/run.py`, `gateway/platforms/telegram_business_history.py`, `tests/gateway/test_telegram_business.py`, `tests/gateway/test_telegram_documents.py`, `tests/gateway/test_native_image_buffer_isolation.py`, `tests/gateway/test_vision_memory_leak.py`, `tests/gateway/test_stt_config.py`
- Boundaries: read-only discovery only; no source edits.
- Done when: owner has an exact file/function map, reuse candidates, and the smallest test set to prove the four tasks.
- Expected evidence: current code paths, gaps, and concrete regression tests.

## Context
- Task name: Telegram Business media ingestion — Tasks 1-4
- Task package: `docs/plans/2026-05-26-telegram-business-media`
- Report path: `docs/plans/2026-05-26-telegram-business-media/reports/explorer.md`
- Worktree: `/home/kcnc/code/hermes/hermes-agent`
- Branch: `epic/telegram-business-media` (`52d93fa27`)
- Verify scope: Tasks 1-4 only

## Project shape
- Runtime/framework/package manager: Python gateway + pytest; Telegram adapter in `gateway/platforms/telegram.py`.
- Main entrypoints: `TelegramAdapter._handle_media_message`, `TelegramAdapter._handle_business_update`, `GatewayRunner._prepare_inbound_message_text`.
- Relevant directories/files: `gateway/platforms/telegram.py`, `gateway/run.py`, `gateway/platforms/telegram_business_history.py`, `gateway/session.py`, `tests/gateway/*`.

## Scope discovery
- Requested behavior maps to: (1) extract reusable Telegram media preparation, (2) let Business draft/auto paths carry photo/doc/voice media, (3) make Business previews/history useful for media-only chats, (4) prove Business image paths still flow through native/text vision routing.
- Likely in scope: adapter inbound helpers, Business routing in `_handle_business_update`, Business registry/history preview text, and new/updated gateway tests.
- Out of scope: outbound Business send semantics, STT backend changes, deployment on `EverydayWiteVPS`.

## Existing implementations and reuse candidates
- `gateway/platforms/telegram.py:_handle_media_message` (lines 6922-7075): already downloads/caches photo, voice, audio, video, and documents, including photo burst/media-group batching via `_queue_media_group_event` / `_enqueue_photo_event`.
- `gateway/platforms/telegram.py:_build_message_event` (7396-7475): already encodes Business thread identity through `business_connection_id` and `direct_messages_topic_id` into `source.thread_id`.
- `gateway/platforms/telegram.py:_business_record_from_message` (833-876): already upserts Business chat registry/history, but it stores `message.text` only.
- `gateway/platforms/telegram.py:_business_chat_card_text` (975-997): already renders `last_message_preview`; it will benefit once preview text is populated for media-only chats.
- `gateway/run.py:_prepare_inbound_message_text` (7710-7855): already routes `MessageType.PHOTO` to native vision or `vision_analyze`, and `MessageType.VOICE` to STT.
- `gateway/session.py:build_session_key` and `GatewayRunner._session_key_for_source` (2055-2068): session keys include `source.thread_id`, so Business threads can stay isolated if the source carries the Business thread id.
- Existing regression tests: `tests/gateway/test_telegram_documents.py` covers normal media caching/batching; `tests/gateway/test_business_update_records_inbound_and_rule_history` and `test_business_watch_chat_notifies_owner_without_agent` cover current Business text behavior; `tests/gateway/test_native_image_buffer_isolation.py` covers session-scoped image buffers.

## Missing pieces
- `gateway/platforms/telegram.py::_handle_media_message`: still inlines media extraction instead of delegating to a shared helper callable from Business updates.
- `gateway/platforms/telegram.py::_handle_business_update`: still rejects any Business message without `message.text` and never routes Business media through the shared media path.
- `gateway/platforms/telegram.py::_business_record_from_message` and `_send_business_watch_notification`: still use `message.text` only, so captioned/media-only Business chats can produce blank previews and miss caption-based matching.
- `tests/gateway/test_telegram_business.py`: no coverage yet for Business photo/document/voice draft-routing, media-only preview text, or caption-preserving history.
- `tests/gateway/test_telegram_business.py` / `tests/gateway/test_native_image_buffer_isolation.py`: no Business-thread-specific assertion that `source.thread_id="business:..."` (and `business:...:topic:...`) keeps the native image buffer isolated.

## Suggested plan tasks
- Extract shared media prep from `_handle_media_message` into a helper (the plan’s proposed `_prepare_telegram_media_event` shape is fine), then call it from both normal Telegram media handling and Business draft/auto routing.
  - Primary verification: existing normal media suite under `tests/gateway/test_telegram_documents.py` still passes.
- Update `_handle_business_update` to classify `text`/`caption`/supported media instead of text-only gating, and to route `draft`/`auto` Business media through the shared helper.
  - Primary verification: new Business photo/document/voice tests in `tests/gateway/test_telegram_business.py`.
- Add a Business preview helper (or equivalent inline logic) so `_business_record_from_message` stores caption/media fallback text and `_send_business_watch_notification` uses caption-aware matching.
  - Primary verification: new preview/history tests in `tests/gateway/test_telegram_business.py`.
- Add Business-source image-routing tests around `GatewayRunner._prepare_inbound_message_text` / `_consume_pending_native_image_paths`.
  - Primary verification: new Business-thread native/text vision tests, plus existing `tests/gateway/test_native_image_buffer_isolation.py` and `tests/gateway/test_vision_memory_leak.py` as regressions.

## Risks and unknowns
- Blocking:
  - Business command/caption edge behavior is currently ambiguous: `_handle_business_update` ignores `message.text` commands only, so once captions are treated as content the owner may want a deliberate policy for captioned slash-commands.
  - The current local `.venv` lacks `pytest`, so `scripts/run_tests.sh` failed before collection; the fallback `venv` does have `pytest 9.0.2`, but the wrapper prefers `.venv` first.
- Non-blocking follow-up candidates:
  - If the new shared helper changes photo-group flush timing, keep the existing media-group batching tests green.
  - No schema migration appears necessary for preview-only changes; the risk is behavior drift, not storage shape.

## Suggested verification
- Targeted:
  - `scripts/run_tests.sh tests/gateway/test_telegram_documents.py tests/gateway/test_telegram_business.py tests/gateway/test_native_image_buffer_isolation.py tests/gateway/test_vision_memory_leak.py tests/gateway/test_stt_config.py`
- Broader/final:
  - Add/adjust the Business-specific tests above, then rerun the same targeted set once the `.venv`/pytest issue is resolved.

## Verification run
- Attempted: `scripts/run_tests.sh tests/gateway/test_telegram_business.py::test_business_update_records_inbound_and_rule_history tests/gateway/test_telegram_business.py::test_business_watch_chat_notifies_owner_without_agent tests/gateway/test_telegram_documents.py::TestDocumentDownloadBlock::test_png_document_is_routed_as_image tests/gateway/test_native_image_buffer_isolation.py tests/gateway/test_stt_config.py::test_prepare_inbound_message_text_transcribes_queued_voice_event`
  - Result: failed before collection because `.venv/bin/python` does not have `pytest` installed (`No module named pytest`).

## Verdict
- Status: partial
- Goal state: not achieved yet (discovery only)
- Final readiness: not ready
- Summary: the code already has the reusable normal-media pipeline and Business thread wiring; the missing work is mainly Business media classification/routing plus preview/test coverage.

## Next-agent brief
- Objective: implement shared Telegram media prep and Business media routing for Tasks 1-4.
- Target: `gateway/platforms/telegram.py` first, then Business-focused tests in `tests/gateway/test_telegram_business.py` and the gateway regression files.
- Settled already: normal Telegram media caching/batching exists; Business thread ids already flow into `source.thread_id`; gateway vision/STT preprocessing already handles images/voice once an event reaches the runner.
- Boundaries: keep outbound Business send behavior unchanged; do not redesign STT backends or deployment.
- Verification target: Business photo/document/voice in draft/auto mode reaches the same cached-media pipeline as normal Telegram messages, Business watch cards/previews are non-blank for media-only chats, and Business-source image routing remains isolated by session key.
- Expected output: concise implementation report with exact functions changed and tests added.
