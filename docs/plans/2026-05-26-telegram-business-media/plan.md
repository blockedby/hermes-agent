# Plan: Telegram Business media ingestion

## SEO / executive summary

Telegram Business chats currently support text-only inbound processing. The normal Telegram adapter already downloads photos, image-documents, documents, audio/voice, and videos into local cache and forwards them through the gateway media pipeline. The Business path should reuse that same media handling instead of dropping non-text Business messages, while preserving Business chat registry/history metadata, thread identity (`business:<connection_id>[:topic:<direct_topic_id>]`), owner watch notifications, and draft/auto routing. Voice messages are first-class: the original voice/audio media record and the STT transcript must both be persisted in the Business history/session database surfaces, not only injected transiently into the agent prompt.

## Goal

Make Telegram Business inbound media usable by Hermes:

- Business photos and image documents reach the existing image pipeline (`event.media_urls` + `event.media_types`).
- Native-vision models receive images inline through `GatewayRunner._prepare_inbound_message_text()` / `build_native_content_parts()`.
- Non-native-vision models get automatic `vision_analyze` text enrichment.
- Business captions are preserved as user text.
- Business documents/audio/video are not silently ignored; they follow the same cached attachment behavior as normal Telegram media where supported.
- Business voice messages are persisted as inbound media records in Business chat/history storage and the session transcript DB.
- Business voice transcriptions are persisted after STT, linked to the original Business message/media where possible.
- Business source/thread metadata remains intact so replies/drafts route to the correct Business customer chat.

## Current evidence

- `gateway/platforms/telegram.py::_handle_business_update()` currently drops non-text Business messages with `elif not getattr(message, "text", None)`.
- `gateway/platforms/telegram.py::_handle_media_message()` already implements the download/cache/event path for normal Telegram photos, image documents, voice/audio/video, and documents.
- `gateway/platforms/telegram.py::_build_message_event()` already recognizes `business_connection_id` and builds Business source thread ids.
- `gateway/run.py::_prepare_inbound_message_text()` already routes `event.media_urls` images to native vision or `vision_analyze` fallback.
- `gateway/run.py::_prepare_inbound_message_text()` routes `MessageType.VOICE` audio paths through `_enrich_message_with_transcription()`, but that STT result is currently prompt text; Telegram Business history persistence needs an explicit write-back so the transcript is queryable later.

## Scope

In scope:

- Refactor Telegram media extraction so Business and normal message paths can share it.
- Accept Business messages with `caption` and/or media even when `text` is absent.
- Preserve current Business modes:
  - `ignored`: no agent/no owner notification beyond existing behavior.
  - `watch`: owner card/notification only.
  - `draft` / `auto`: enqueue a `MessageEvent` to the agent.
- Add targeted tests for Business photo, image document, voice message, voice transcription persistence, caption-only media, and text-only regression.

Out of scope:

- Changing outbound Business send semantics or approval policy.
- Forcing direct `read_image` calls. The automatic path is native vision or `vision_analyze`; `read_image` remains a manual tool.
- Replacing the STT provider implementation. This work persists the existing STT output; it does not change transcription backends.
- Live VPS deployment. This plan covers repo changes; rollout to `EverydayWiteVPS` is a separate ops step.

## Ownership model

Keep as one slice under one implementation owner. The risky part is preserving Business routing while reusing media handling; splitting by file would increase coordination without independent behavior boundaries.

## Proposed design

### 1. Introduce shared inbound media preparation helper

Extract most of `_handle_media_message()` after initial gating into a helper, for example:

```python
async def _prepare_telegram_media_event(
    self,
    msg: Message,
    *,
    update_id: Optional[int],
    allow_photo_batching: bool = True,
) -> Optional[MessageEvent]:
    ...
```

The helper should:

- Determine `MessageType` from `sticker/photo/video/audio/voice/document`.
- Build `MessageEvent` via `_build_message_event(msg, msg_type, update_id=...)`.
- Copy `caption` into `event.text` after `_clean_bot_trigger_text()`.
- Cache media and set `event.media_urls` / `event.media_types` exactly as current normal media path does.
- For photo/image-document album/burst batching, either:
  - return a marker that the caller enqueued/buffered the event, or
  - support a `dispatch_photo_event` callback.

Important: avoid duplicating media code in `_handle_business_update()`. Duplication would regress future Telegram media fixes.

### 2. Keep normal Telegram media behavior unchanged

Rewrite `_handle_media_message()` to keep existing gating/observe behavior, then call the shared helper and dispatch the returned event. Photo/media-group batching should keep existing behavior and tests.

### 3. Update Business update routing

In `_handle_business_update()` replace the text-only guard with message-content classification:

- `message_text = message.text or message.caption or ""`
- `has_media = bool(message.photo or message.document or message.voice or message.audio or message.video or message.sticker)`
- ignore only if neither text/caption nor supported media is present.
- command ignore should apply only to real `message.text` commands, not captions that begin with `/` unless existing product behavior requires captions-as-commands.

For Business `draft` / `auto`:

- If `has_media`, call the shared media helper with the Business message.
- Do not call normal group/DM `_should_process_message()`; Business has already passed its own gates.
- Enqueue/dispatch through the same queue method used today (`_enqueue_text_event`) when the event should enter the agent path. If a photo helper batches internally, ensure the final flush calls the same handler path and not a non-Business session.
- Record `draft_requested` history with message id and mode as today.

For Business `watch`:

- Continue owner notification only.
- Update preview/history to use `text or caption or "[photo]"/"[document]"` so the dashboard/card is not blank.
- Optional follow-up task: owner card can include attachment type/count, but that is not required for first correctness.

### 4. Preserve Business chat registry/history previews

Update `_business_record_from_message()` so `text=` and history `preview` use a helper such as:

```python
def _business_message_preview(message: Message) -> str:
    return message.text or message.caption or _telegram_media_preview(message)
```

This avoids blank `last_message_text` for media-only chats and keeps callbacks/dashboards useful.

### 5. Avoid native image buffer/session regressions

Because `_build_message_event()` already encodes `business_connection_id` into `source.thread_id`, `GatewayRunner._prepare_inbound_message_text()` should automatically key pending native images by the Business session key. Verify with tests that `source.thread_id` is `business:<connection_id>` or `business:<connection_id>:topic:<id>` and `event.media_urls` survives queueing.

### 6. Persist Business voice media and STT transcripts

Voice handling needs two durable records:

1. **Inbound voice media record at adapter time**: when Telegram Business receives `message.voice` (and optionally Telegram audio that should remain a file attachment), persist an inbound history event with `media_type="voice"`, `media_urls`/cache path metadata, `message_id`, `business_connection_id`, `customer_chat_id`, and `direct_messages_topic_id`.
2. **Transcription record after STT**: when `GatewayRunner._prepare_inbound_message_text()` transcribes a Business `MessageType.VOICE`, write a linked history event such as `voice_transcribed` or an `inbound` event field with the transcript, provider/status, source `message_id`, and created timestamp.

Implementation options:

- Extend `TelegramBusinessHistoryStore` normalization to preserve safe structured fields such as `media_type`, `media_urls`, `transcript`, `transcription_status`, and `transcription_provider`.
- Add a Telegram adapter method such as `_record_business_voice_transcription(source, message_id, transcript, status, provider)` and call it from the gateway runner only when `source.platform == Platform.TELEGRAM` and `source.thread_id` is a Business thread.
- Prefer structured persistence over scraping the formatted prompt string (`[The user sent a voice message~ ...]`). If needed, refactor `_enrich_message_with_transcription()` to return both display text and structured transcript results.

The session transcript DB should also contain the enriched user turn, so normal chat replay includes what the user said. Business history storage should contain the structured transcript, so the dashboard/chat database can display/search it without parsing agent prompt text.

## Plan tasks

### Task 1: Refactor Telegram media extraction into a shared helper

Goal:
- Normal Telegram media behavior remains unchanged while media preparation becomes callable from Business updates.

Boundary:
- System area: Telegram platform adapter inbound media.
- Primary verification: existing Telegram media/document tests continue passing.

Existing pattern / reuse:
- Reuse current logic in `TelegramAdapter._handle_media_message()`.
- Reuse `cache_image_from_bytes`, `cache_audio_from_bytes`, `cache_video_from_bytes`, `cache_document_from_bytes`.

Missing change:
- Extract download/cache/event-building code without changing observable normal media behavior.

Scope / likely files:
- `gateway/platforms/telegram.py`
- `tests/gateway/test_telegram_documents.py`
- existing Telegram media tests as regression coverage.

Acceptance criteria:
- Photos, image documents, regular documents, audio/voice, and video still populate `MessageEvent.media_urls`/`media_types` as before.
- Existing photo burst/media-group batching still works.
- Existing unsupported/oversized document behavior is unchanged.

Test plan:
- Positive: `scripts/run_tests.sh tests/gateway/test_telegram_documents.py -q`
- Regression: `scripts/run_tests.sh tests/gateway/test_telegram_photo_interrupts.py tests/gateway/test_session_race_guard.py -q`

Dependencies:
- Depends on: none
- Blocks: Task 2
- Can run parallel with: none

Executor:
- aad-implementer

### Task 2: Allow Telegram Business media through the shared media path

Goal:
- Business messages with media/captions are no longer discarded as non-text.

Boundary:
- System area: Telegram Business update routing.
- Primary verification: new Business media tests.

Existing pattern / reuse:
- `_handle_business_update()` mode logic.
- `_build_message_event()` Business thread metadata.
- Shared helper from Task 1.

Missing change:
- Replace text-only guard with text/caption/media classification and route media events for `draft`/`auto` modes.

Scope / likely files:
- `gateway/platforms/telegram.py`
- `tests/gateway/test_telegram_business.py`

Acceptance criteria:
- Business photo in `draft` mode enqueues a Business `MessageEvent` with `MessageType.PHOTO`, cached image path, image MIME, caption text, and Business thread id.
- Business image document in `draft` mode follows image path and can trigger the same vision pipeline downstream.
- Business voice message in `draft` mode enqueues a Business `MessageEvent` with `MessageType.VOICE`, cached audio path, audio MIME, caption text if present, and Business thread id.
- Business text-only messages behave exactly as before.
- Business non-text unsupported empty update is still ignored.

Test plan:
- Positive:
  - new test: Business photo + caption in draft mode enqueues media event.
  - new test: Business image document in draft mode enqueues media event as photo.
  - new test: Business voice message in draft mode enqueues media event as voice.
  - existing `test_business_unknown_chat_sends_owner_mode_card_before_agent` still passes.
- Negative:
  - new test: Business message with no text/caption/media is ignored.
  - command text still ignored.

Dependencies:
- Depends on: Task 1
- Blocks: Task 3
- Can run parallel with: Task 4 test drafting after helper API is settled.

Executor:
- aad-implementer

### Task 3: Preserve Business registry/history previews for media messages

Goal:
- Business dashboard/history remains useful for media-only and captioned messages.

Boundary:
- System area: Telegram Business chat registry/history.
- Primary verification: focused Business history tests.

Existing pattern / reuse:
- `_business_record_from_message()` and `_record_business_history_event()`.
- `_send_business_watch_notification()` rule/history flow.

Missing change:
- Add a preview helper based on `text`, `caption`, and media kind fallback.

Scope / likely files:
- `gateway/platforms/telegram.py`
- `tests/gateway/test_telegram_business.py`

Acceptance criteria:
- Captioned Business media records caption as `last_message_text` and history preview.
- Media-only Business photo/document/voice records a non-empty preview such as `[photo]`, `[document]`, or `[voice]`.
- Rule matching remains text/caption based and does not accidentally match placeholder previews unless desired.

Test plan:
- Positive: new test for captioned Business photo history preview.
- Edge: new test for media-only Business photo preview.
- Edge: new test for media-only Business voice preview.
- Regression: existing Business rule history test remains green.

Dependencies:
- Depends on: Task 2
- Blocks: Task 5
- Can run parallel with: none

Executor:
- aad-implementer

### Task 4: Verify gateway vision handoff for Business media

Goal:
- Prove Business media reaches the existing vision/native-image gateway path without special casing.

Boundary:
- System area: adapter event → gateway runner preprocessing integration.
- Primary verification: focused unit/integration tests around `GatewayRunner._prepare_inbound_message_text()`.

Existing pattern / reuse:
- `tests/gateway/test_native_image_buffer_isolation.py`
- `tests/gateway/test_vision_memory_leak.py`
- `GatewayRunner._prepare_inbound_message_text()`.

Missing change:
- Add/adjust tests to feed a Business-source `MessageEvent` with image media into `_prepare_inbound_message_text()`.

Scope / likely files:
- `tests/gateway/test_telegram_business.py` or a focused gateway test file.
- No production change expected unless a session-key bug is uncovered.

Acceptance criteria:
- Native mode stores pending image paths under the Business session key.
- Text mode invokes/uses `vision_analyze` enrichment for the Business image path.
- No cross-session leakage between normal DM and Business chat with same chat id.

Test plan:
- Positive: native routing test for `source.thread_id="business:bc-1"`.
- Positive: text routing test with mocked `vision_analyze_tool`.
- Regression: `scripts/run_tests.sh tests/gateway/test_native_image_buffer_isolation.py tests/gateway/test_vision_memory_leak.py -q`

Dependencies:
- Depends on: Task 2
- Blocks: final acceptance
- Can run parallel with: Task 3 after event shape is known.

Executor:
- aad-implementer

### Task 5: Persist Business voice media and transcription records

Goal:
- Voice messages and their STT transcripts are durable Business chat data, not only transient prompt text.

Boundary:
- System area: Telegram Business history/store + gateway transcription preprocessing.
- Primary verification: focused Business voice persistence tests and STT gateway tests.

Existing pattern / reuse:
- Telegram voice caching in `_handle_media_message()`.
- `GatewayRunner._enrich_message_with_transcription()` and `tests/gateway/test_stt_config.py`.
- `TelegramBusinessHistoryStore` normalization and append/list APIs.

Missing change:
- Persist a Business inbound voice media event when the voice is received.
- Persist a linked Business transcription event after successful STT.
- Preserve structured fields in `TelegramBusinessHistoryStore` instead of dropping them during normalization.

Scope / likely files:
- `gateway/platforms/telegram.py`
- `gateway/platforms/telegram_business_history.py`
- `gateway/run.py`
- `tests/gateway/test_telegram_business.py`
- `tests/gateway/test_stt_config.py` or a focused Business STT test file.

Acceptance criteria:
- Business voice message creates a history/database record with message id, media kind, cached audio path or safe media reference, and Business chat key.
- Successful STT creates a durable transcript record linked to the same Business message id/chat key.
- Failed/disabled STT creates a durable status record or preserves a clear failure status, without pretending there is a transcript.
- The session transcript DB still stores the enriched user turn so conversation replay includes the transcription.
- History normalization preserves safe structured voice/transcript fields and does not store secrets.

Test plan:
- Positive:
  - new test: Business voice inbound stores `[voice]`/media metadata in Business history.
  - new test: mocked STT for Business voice stores transcript in Business history and enriched user turn.
- Negative:
  - new test: disabled/no-provider STT stores a failure/status record without transcript text.
- Regression:
  - `scripts/run_tests.sh tests/gateway/test_stt_config.py tests/gateway/test_telegram_audio_vs_voice.py -q`

Dependencies:
- Depends on: Tasks 1-3
- Blocks: final acceptance
- Can run parallel with: Task 4 after Business event shape is known.

Executor:
- aad-implementer

### Task 6: Final verification and rollout notes

Goal:
- Confirm the repo change is ready and document how to validate on `EverydayWiteVPS`.

Boundary:
- System area: test evidence + operational handoff.
- Primary verification: targeted test suite and manual/live checklist.

Existing pattern / reuse:
- `scripts/run_tests.sh` per repo policy.
- Runtime note in `AGENTS.md` and this task package.

Missing change:
- Run targeted tests and write verification evidence.
- Draft VPS smoke checklist.

Scope / likely files:
- `docs/plans/2026-05-26-telegram-business-media/verification/local.md`
- optional rollout note in `plan.md` final status.

Acceptance criteria:
- Targeted Telegram/Business/media tests pass through `scripts/run_tests.sh`.
- Manual smoke checklist covers live VPS deployment: restart gateway, send Business photo with caption, verify owner card/draft/agent sees image; send Business voice message, verify cached voice record and STT transcript appear in Business history/session data.
- No claim that local gateway logs prove live behavior.

Test plan:
- `scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_documents.py tests/gateway/test_native_image_buffer_isolation.py tests/gateway/test_vision_memory_leak.py tests/gateway/test_stt_config.py tests/gateway/test_telegram_audio_vs_voice.py -q`

Dependencies:
- Depends on: Tasks 1-5
- Blocks: done-state
- Can run parallel with: none

Executor:
- root owner

## Final acceptance criteria

- Business media is no longer dropped solely because `message.text` is absent.
- Business photo/image-document in draft/auto mode reaches the gateway as cached image media.
- Captions are preserved and media-only messages get useful previews.
- Business voice messages are persisted as media records in Business history/session data.
- Business voice STT transcripts are persisted as structured Business history records and in the enriched session transcript DB turn.
- Existing normal Telegram media tests remain green.
- Vision and STT paths are proven via gateway preprocessing tests.
- Rollout note explicitly says live validation must happen on `EverydayWiteVPS`.

## Risks / watchpoints

- Photo batching currently dispatches via `handle_message`; when invoked from Business flow it must not bypass mode gating or lose Business metadata.
- `_business_event_from_chat_entry()` currently only recreates text events from registry entries; if mode callbacks should enqueue the latest media later, this needs a separate media-state design. First pass can require media to be handled at inbound time.
- Watch notifications may remain text-only for first pass; do not accidentally send customer media to owner unless product policy allows it.
- Voice transcript persistence creates more sensitive stored text than media-only metadata; keep fields bounded, private, and avoid storing raw credentials/URLs beyond safe local cache references.
- Do not make tool availability assumptions: automatic image handling is native vision/`vision_analyze`; `read_image` is available but not the auto path.

---

# Added slice: Telegram Business dashboard Generate draft now behavior (2026-05-26)

## Task intake

Goal: make the Telegram Business dashboard chat-detail "Generate draft now" action an in-place Web App action that does not navigate/refresh away, shows submitting/queued/generating/result/error states in the mounted detail UI, and accepts an optional prompt/topic/theme while preserving empty-prompt generation.

In scope:
- `apps/telegram-business-dashboard` chat-detail controls/client API/BFF route for draft generation.
- Python Hermes dashboard API draft request path if needed to pass optional prompt to the existing draft system.
- Nearby Telegram Business dashboard buttons/forms for unintended submit/navigation behavior.
- Targeted dashboard tests and focused Python dashboard API tests for prompt pass-through if backend changes.

Out of scope:
- VPS deploy/restart.
- Broad visual redesign or unrelated dashboard architecture refactor.
- Changing approval policy beyond prompt metadata pass-through for dashboard-requested drafts.

Done-state:
- AC1-AC5 from the routing packet satisfied or explicitly waived with evidence.
- Final report: `reports/dashboard-draft-owner.md`.
- Verification evidence: `verification/dashboard-draft.md`.

Blocking unknowns:
- None known after initial orientation; exact backend storage/consumption field names to be confirmed in implementation.

## Repo orientation and reuse discovery

Local guidance:
- Root `AGENTS.md`: live runtime is on `EverydayWiteVPS`; do not assume/deploy local runtime. Use `scripts/run_tests.sh` for Python tests.
- `apps/telegram-business-dashboard/AGENTS.md`: this is Next.js 16.2.6; read relevant `node_modules/next/dist/docs/` before Next-specific changes. Initial doc read: `node_modules/next/dist/docs/01-app/index.md` (App Router overview; route handlers/client components remain file-system App Router surfaces).

Likely files/areas:
- Frontend detail state/UI: `apps/telegram-business-dashboard/src/components/business/chat-detail-shell.tsx`, `chat-detail-view.tsx`.
- Frontend API client/types/tests: `apps/telegram-business-dashboard/src/lib/business/api.ts`, `types.ts`, `business-api.test.ts`.
- BFF route/tests: `apps/telegram-business-dashboard/src/app/api/business/chats/[token]/draft/route.ts`, `route-handlers.test.ts`.
- Backend dashboard API/tests: `gateway/platforms/telegram_business_dashboard_api.py`, `tests/gateway/test_telegram_business_dashboard_api.py`.

Existing patterns to reuse:
- Client APIs use `businessFetch()` with Telegram init data only in headers and JSON body only for action payloads.
- BFF route authenticates via `authenticateTelegramAdmin()`, strips `initData` via `postBodyWithoutInitData()`, adds `actorUserId`, and proxies through `callHermesDashboard()`.
- Detail shell already owns mounted state and calls `generateBusinessDraft()`; detail view already uses explicit `Button` controls and action `Alert`.
- Backend `BusinessDashboardAPI.request_draft()` records `draft_requested` history and returns queued status.

Missing pieces:
- Frontend draft API accepts prompt parameter and sends `{source:"latest", prompt?: string}` (including preserving non-empty prompt; empty/omitted valid).
- BFF proxy allows prompt in forwarded body.
- Backend accepts optional prompt/topic/theme and records/passes it where existing draft generation can consume it.
- Detail UI has a prompt input and more explicit queued/generating/result/error feedback without remount/navigate.
- Related controls audited for missing `type="button"` / accidental form navigation; fixes/waivers recorded.
- Tests updated for API pass-through, UI rendering/state, and backend prompt acceptance.

## Plan tasks and dependency graph

### Task DD-1: Implement dashboard draft in-place prompt/status behavior

Goal:
- Clicking/tapping Generate draft now remains in the mounted chat detail UI, sends optional prompt/topic when non-empty, accepts empty prompt, and displays submitting/queued/result/error feedback.

Boundary:
- System area: Telegram Business dashboard frontend + BFF + Hermes dashboard API draft request.
- Primary verification: targeted dashboard Vitest tests plus focused Python dashboard API tests if backend changes.

Acceptance criteria:
- AC1: Generate draft control is not a link/form-submit navigation; any relevant buttons explicitly avoid accidental submit where applicable.
- AC2: Detail UI exposes draft action states: submitting/queueing, queued/generating/pending from API status, success/result text or recoverable error.
- AC3: Empty prompt works; non-empty prompt is sent through client API, BFF, and backend request/history/draft context without breaking `source: latest`.
- AC4: Nearby dashboard controls are audited for redirect/refresh risks; direct inconsistencies fixed or waived with evidence.
- AC5: Targeted tests/checks pass.

Test plan:
- `cd apps/telegram-business-dashboard && npm run test:auth -- src/lib/business/business-api.test.ts src/app/api/business/route-handlers.test.ts src/components/business/business-dashboard-ui.test.tsx`
- `cd apps/telegram-business-dashboard && npm run typecheck`
- If `gateway/platforms/telegram_business_dashboard_api.py` changes: `scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py -q` from repo root.

Dependencies:
- Depends on: none.
- Blocks: final owner verification/report.
- Executor: `aad-implementer`.

Execution ledger:
- 2026-05-26 owner: plan gate completed for DD-1; dispatching one `aad-implementer` because this is a coherent single-slice implementation with one verification story.
- 2026-05-26 owner: DD-1 implemented directly due nested subagent depth limit. Verification recorded in `verification/dashboard-draft.md`. Status: done pending parent review/deploy.

---

# Addendum: Telegram Business dashboard auth 24-hour session lease

## Task intake

Goal: keep fresh Telegram WebApp `initData` validation on the existing 5-minute max age, and add a 24-hour server-side dashboard session lease. `POST /api/session` issues an HttpOnly Secure signed cookie; Business BFF routes accept either fresh `initData` or a valid unexpired dashboard session cookie. Fresh `initData` remains authoritative and refreshes the cookie. Service tokens remain server-only.

Out of scope: deployment, push, PR creation, live VPS rollout, and client UI redesign.

## Repo orientation / reuse

- `apps/telegram-business-dashboard/src/lib/server/telegram-auth.ts`: existing `validateTelegramAdminInitData()` and admin allowlist.
- `apps/telegram-business-dashboard/src/lib/server/business-route.ts`: central Business BFF auth gate.
- `apps/telegram-business-dashboard/src/app/api/session/route.ts`: session POST.
- Tests: `src/app/api/session/route.test.ts`, `src/app/api/business/route-handlers.test.ts`, `src/lib/server/telegram-auth.test.ts`.

## Plan tasks and execution ledger

Task 1: signed dashboard session cookie issuance.
- Acceptance: valid fresh initData returns the existing user JSON and includes HttpOnly Secure 24-hour signed cookie; invalid/stale/non-admin/config-error cases remain rejected.
- Executor: `aad-implementer`.
- Status: done in commit `3011c9568`.

Task 2: Business BFF cookie fallback.
- Acceptance: Business routes proxy with actor user id using cookie-only auth; fresh initData still proxies and refreshes cookie; expired/tampered/malformed cookies reject without calling Hermes; service token remains server-only.
- Executor: `aad-implementer`.
- Status: done in commit `3011c9568`.

Final owner verification:
- `cd apps/telegram-business-dashboard && npm run test:auth -- src/app/api/session/route.test.ts src/app/api/business/route-handlers.test.ts src/lib/server/telegram-auth.test.ts`: passed, 3 files / 27 tests.
- `cd apps/telegram-business-dashboard && npm run typecheck`: passed.
- `cd apps/telegram-business-dashboard && npm run lint`: passed.

Reports:
- Implementer: `reports/aad-implementer-dashboard-session-lease.md`.
- Owner final: `reports/dashboard-session-lease-owner.md`.
