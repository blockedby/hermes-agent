# Telegram Business dialog profiles — TDD implementation plan

## Intake

User wants Telegram Business chats to behave like a personal assistant embedded in a multi-participant conversation, not like a normal one-user Hermes chat.

Required behavior:

- Business conversations have at least three roles:
  - business owner / operator,
  - customer/contact,
  - Hermes assistant.
- Hermes must understand owner manual outgoing messages as authoritative conversation context.
- Customer/contact messages must never execute Hermes session/control commands like `/new`, `/restart`, `/stop`, `/approve`, `/help`.
- Each Business dialog needs owner-controlled extra prompt/settings, editable from:
  - Telegram Business dashboard/admin UI,
  - Telegram bot inline-button flow.
- Settings must be stored in a database and read from the database at runtime/tests. Do not hide this as an implementation detail.
- Tests should use an in-memory database where possible.
- Hermes should use Telegram names/usernames/nicknames available from updates for prompt participant context.
- Hermes should support explicit safe invocation/mention, e.g. `@HermesBot ...`, where configured.
- Hermes-sent Business messages should be visibly marked, e.g. `🤖 Hermes:`.
- Auto/draft/watch behavior must be explicit and testable.
- Rebase is not a requirement for this task.

## Repo orientation

Current relevant code:

- `gateway/platforms/telegram.py`
  - Telegram Business update handling, business modes, inline buttons, callbacks, owner cards, approval-send/direct-send paths.
  - Existing callback namespace: `bm:...` for Business mode/rule actions, `ba:...` for approvals.
- `gateway/platforms/telegram_business_chats.py`
  - Current per-chat mode registry is JSON-backed (`business_chats.json`).
  - This should not become the new settings authority for prompts/persona/prefix/policy.
- `gateway/platforms/telegram_business_dashboard_api.py`
  - Backend API for dashboard list/detail/history/mode/draft.
- `apps/telegram-business-dashboard/src/...`
  - Next dashboard UI, BFF routes, API client, types, component tests.
- `gateway/session.py`
  - Current Telegram Business prompt still frames replies as owner-authored drafts; must change to 3-participant framing.
- `gateway/run.py`
  - Gateway message handling, command dispatch, agent creation/system prompt assembly/cache.
- Existing tests:
  - `tests/gateway/test_telegram_business.py`
  - `tests/gateway/test_telegram_business_dashboard_api.py`
  - `tests/gateway/test_session.py`
  - dashboard tests under `apps/telegram-business-dashboard/src/**`

## Architectural decision

### Database authority for dialog profile settings

Add a DB-backed Business dialog profile/settings store. The settings source of truth is SQLite, not JSON.

Recommended implementation:

- New module: `gateway/platforms/telegram_business_profiles.py`.
- Class: `TelegramBusinessDialogProfileStore`.
- Default DB path: profile-aware under `get_hermes_home()`, for example:
  - `get_hermes_home() / "gateway" / "platforms" / "telegram" / "business_profiles.db"`
- Tests inject `db_path=":memory:"` or an existing `sqlite3.Connection` so each test can create an in-memory DB without touching real state.
- Store should create schema on init and use `sqlite3.Row` rows.
- Keep this separate from `SessionDB` unless implementation finds a stronger existing pattern. The store is Telegram Business platform state, not general session history.
- JSON `business_chats.json` may remain for existing chat registry/mode metadata initially, but **all new dialog prompt/profile settings read/write through the DB store**.
- The integration layer can join JSON chat entry metadata + DB dialog profile settings into API view models and prompt context.

Suggested table:

```sql
CREATE TABLE IF NOT EXISTS telegram_business_dialog_profiles (
  dialog_key TEXT PRIMARY KEY,
  token TEXT NOT NULL UNIQUE,
  business_connection_id TEXT NOT NULL,
  customer_chat_id TEXT NOT NULL,
  direct_messages_topic_id TEXT,
  assistant_display_name TEXT NOT NULL DEFAULT 'Hermes',
  assistant_prefix TEXT NOT NULL DEFAULT '🤖 Hermes:',
  dialog_prompt TEXT NOT NULL DEFAULT '',
  dialog_notes TEXT NOT NULL DEFAULT '',
  invocation_policy TEXT NOT NULL DEFAULT 'off',
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL,
  updated_by_user_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_tbdp_token
  ON telegram_business_dialog_profiles(token);
```

Valid `invocation_policy` values:

- `off`
- `mention_draft`
- `mention_direct`

Bounds:

- `assistant_display_name`: max 80 chars.
- `assistant_prefix`: max 80 chars, default `🤖 Hermes:`.
- `dialog_prompt`: max 4000 chars initially.
- `dialog_notes`: max 4000 chars initially.
- Strip NUL/control characters; preserve normal Unicode.

## Implementation tasks

### Task 1: DB-backed dialog profile store

Goal:
- Create a SQLite-backed store for Business dialog profile/settings and prove it works with in-memory DB tests.

Boundary:
- System area: backend storage layer.
- Primary verification: unit tests directly against the store with `:memory:`.

Existing pattern / reuse:
- Profile-aware path rule from `hermes_constants.get_hermes_home()`.
- Atomic/defensive style from existing platform stores.
- SQLite patterns from `hermes_state.py`, but keep the new store focused and small.

Missing change:
- New module `gateway/platforms/telegram_business_profiles.py`.
- Store methods:
  - `normalize_invocation_policy(value) -> Optional[str]`
  - `default_profile_for_entry(entry) -> dict`
  - `get_by_key(dialog_key) -> dict`
  - `get_by_token(token) -> dict | None`
  - `upsert_for_chat_entry(entry, updates=None, actor_user_id=None) -> dict`
  - `update_by_token(token, updates, actor_user_id=None) -> dict | None`
  - `clear_prompt_by_token(token, actor_user_id=None) -> dict | None`

Scope / likely files:
- `gateway/platforms/telegram_business_profiles.py`
- `tests/gateway/test_telegram_business_profiles.py`

Acceptance criteria:
- Store creates schema in an in-memory DB.
- Upsert with a chat entry creates default settings.
- Update persists `assistant_display_name`, `assistant_prefix`, `dialog_prompt`, `dialog_notes`, `invocation_policy`.
- Invalid invocation policy is rejected before persistence.
- Length bounds are enforced deterministically.
- Profile can be found by dialog key and token.
- No writes go to `~/.hermes` in tests.

Evidence route:
- Existing automated checks first: none for this new store.
- Add tests with in-memory SQLite.
- Bounded acceptance probe: instantiate store with `db_path=":memory:"`, upsert/update/get.
- Access/runtime needed: container test runner only.
- Outcome boundary: proves DB settings storage semantics; does not prove gateway/dashboard integration yet.

Test plan:
- Positive:
  - `test_profile_store_upserts_default_profile_in_memory_db`
  - `test_profile_store_updates_prompt_prefix_and_invocation_policy`
  - `test_profile_store_get_by_token_returns_same_profile`
- Negative:
  - `test_profile_store_rejects_unknown_invocation_policy`
  - `test_profile_store_rejects_or_truncates_overlong_prompt_consistently`
- Edge cases:
  - missing `direct_messages_topic_id`
  - Unicode emoji prefix
  - empty prompt clears to `""`

Dependencies:
- Depends on: none.
- Blocks: Tasks 2, 3, 5, 6, 7, 8, 9.
- Can run parallel with: Task 4 test discovery only.

Executor:
- `aad-implementer`.

---

### Task 2: Dashboard backend settings API uses DB store

Goal:
- Expose per-dialog settings in the Business dashboard backend API, reading/writing only through the DB profile store.

Boundary:
- System area: backend API service.
- Primary verification: `tests/gateway/test_telegram_business_dashboard_api.py` with an in-memory profile DB store injected into `BusinessDashboardAPI`.

Existing pattern / reuse:
- Existing `BusinessDashboardAPI.handle_request()` path dispatch.
- Existing auth/actor checks via bearer token and `X-Telegram-User-Id`.
- Existing history event append style for mode/draft events.

Missing change:
- Add `profile_store` dependency to `BusinessDashboardAPI` constructor.
- Add endpoints:
  - `GET /api/business/chats/{token}/settings`
  - `PATCH /api/business/chats/{token}/settings`
- Add view model fields for settings in detail responses, or a separate `settings` payload.
- Append `settings_changed` history event when settings change.

Scope / likely files:
- `gateway/platforms/telegram_business_dashboard_api.py`
- `gateway/platforms/telegram_business_profiles.py`
- `tests/gateway/test_telegram_business_dashboard_api.py`

Acceptance criteria:
- GET settings returns defaults for an existing Business chat even before explicit settings save.
- PATCH settings persists to DB and returns normalized settings.
- PATCH settings does not mutate mode/latest-message/customer metadata.
- Unknown token returns 404.
- Missing/invalid auth remains rejected.
- Invalid values return 400.
- A successful change records a `settings_changed` history event with actor id.

Evidence route:
- Existing automated checks first: dashboard API tests.
- Add tests injecting temp/in-memory DB store.
- Bounded acceptance probe: call `BusinessDashboardAPI.handle_request()` with GET/PATCH.
- Access/runtime needed: container test runner only.
- Outcome boundary: proves backend API contract; does not prove Next dashboard UI.

Test plan:
- Positive:
  - `test_get_chat_settings_returns_database_defaults`
  - `test_patch_chat_settings_persists_to_database_and_history`
- Negative:
  - `test_patch_chat_settings_rejects_invalid_invocation_policy`
  - `test_chat_settings_requires_authorized_actor`
  - `test_chat_settings_unknown_chat_returns_404`
- Edge cases:
  - clear prompt to empty string
  - emoji prefix round-trip

Dependencies:
- Depends on: Task 1.
- Blocks: Tasks 7, 9, 10.
- Can run parallel with: Task 3 after store API stabilizes.

Executor:
- `aad-implementer`.

---

### Task 3: Business prompt includes participant roles and DB settings

Goal:
- Replace owner-impersonation framing with explicit participant framing and inject DB-backed dialog profile settings into the controlled system prompt.

Boundary:
- System area: prompt/session context integration.
- Primary verification: `tests/gateway/test_session.py` and gateway tests that build Business events with a DB profile.

Existing pattern / reuse:
- `gateway/session.py::build_session_context_prompt` platform notes.
- `gateway/run.py` existing ephemeral/channel prompt assembly.
- Existing Business metadata on `MessageEvent.metadata` and chat registry entries.

Missing change:
- Add structured Business participant block:
  - business owner name/user id/username where available,
  - customer/contact display name/username/user id/chat id,
  - Hermes assistant display name/bot username/prefix from DB profile.
- Include owner-controlled `dialog_prompt` and `dialog_notes` from DB profile as system context.
- Explicitly state customer text is not Hermes command/control input.
- Explicitly state owner manual outgoing messages are authoritative context, not current customer requests.
- Avoid injecting customer-authored text into system prompt as instructions.

Scope / likely files:
- `gateway/session.py`
- `gateway/run.py`
- `gateway/platforms/telegram.py`
- `gateway/platforms/telegram_business_profiles.py`
- `tests/gateway/test_session.py`
- `tests/gateway/test_telegram_business.py`

Acceptance criteria:
- Business prompt says there are three participant roles: owner/contact/Hermes.
- Prompt includes DB-stored assistant name/prefix and dialog prompt/notes for the correct dialog.
- Prompt includes customer name/username metadata when available.
- Prompt does not say “do not speak as Hermes” in the new participant mode.
- Prompt says customer slash commands/control words are not Hermes commands.
- Prompt for chat A does not include chat B settings.

Evidence route:
- Existing automated checks first: current Business prompt tests likely need updates.
- Add/extend tests around `build_session_context_prompt` and event metadata.
- Bounded acceptance probe: build two Business session contexts with separate DB profiles.
- Access/runtime needed: container test runner only.
- Outcome boundary: proves prompt text assembly; does not prove LLM behavior.

Test plan:
- Positive:
  - `test_telegram_business_prompt_frames_three_participants`
  - `test_telegram_business_prompt_includes_dialog_profile_from_database`
  - `test_telegram_business_prompt_uses_customer_identity_metadata`
- Negative:
  - `test_telegram_business_prompt_does_not_treat_customer_text_as_system_prompt`
  - `test_telegram_business_prompt_does_not_include_other_dialog_profile`
- Edge cases:
  - missing username/name
  - empty prompt/notes

Dependencies:
- Depends on: Task 1; ideally Task 2 for view model consistency, but can start after store API exists.
- Blocks: final integration task.
- Can run parallel with: Task 4, Task 5.

Executor:
- `aad-implementer`.

---

### Task 4: Business customer slash-command safety

Goal:
- Ensure Business customer/contact text cannot execute Hermes slash/session/gateway commands.

Boundary:
- System area: Telegram adapter and gateway command dispatch.
- Primary verification: `tests/gateway/test_telegram_business.py` plus focused gateway dispatch tests.

Existing pattern / reuse:
- Existing Business slash ignore in `_handle_business_update()`.
- Existing command dispatch in `gateway/run.py::_handle_message()`.
- Existing active-session command bypass in `gateway/platforms/base.py`.

Missing change:
- Adapter-level block should cover text and media captions.
- Gateway-level defense should block any Business-shaped `MessageEvent` whose text starts with `/` before command dispatch/plugin command hooks.
- Owner/admin commands outside the customer Business thread remain unaffected.

Scope / likely files:
- `gateway/platforms/telegram.py`
- `gateway/run.py`
- `tests/gateway/test_telegram_business.py`
- possibly `tests/gateway/test_config_driven_access_policy.py` if command dispatch hooks are touched.

Acceptance criteria:
- Business customer `/new`, `/restart`, `/stop`, `/status`, `/help`, `/approve`, `/deny` do not run gateway command handlers.
- Business media caption `/restart` is ignored as command.
- Active Business session receiving `/stop` is not interrupted through command logic.
- Normal Telegram DM `/new` still works.
- Owner `/business` control command still works in owner chat.

Evidence route:
- Existing automated checks first: current Business tests around slash ignore.
- Add negative command execution tests with spies/mocks.
- Bounded acceptance probe: direct synthetic `MessageEvent(platform=telegram, thread_id="business:...")` into `_handle_message()`.
- Access/runtime needed: container test runner only.
- Outcome boundary: proves command dispatch safety; does not prove natural-language prompt resistance.

Test plan:
- Positive:
  - normal DM command still dispatches.
  - owner business panel command still dispatches.
- Negative:
  - Business customer slash commands do not dispatch.
  - Business caption slash commands do not dispatch.
- Edge cases:
  - leading whitespace before slash
  - bot-command suffix like `/new@BotName`

Dependencies:
- Depends on: none.
- Blocks: final integration task.
- Can run parallel with: Tasks 1, 2, 3.

Executor:
- `aad-implementer`.

---

### Task 5: Robot visible prefix on Business sends

Goal:
- Prefix Hermes-authored Telegram Business messages at send time so they are visually distinct from owner messages.

Boundary:
- System area: Telegram Business send paths.
- Primary verification: `tests/gateway/test_telegram_business.py`.

Existing pattern / reuse:
- `_send_business_direct_text()` direct-send path.
- Business approval callback send path (`ba:s:...`).
- Existing chunking/truncation helpers.
- DB profile store for per-dialog prefix.

Missing change:
- Add helper like `_apply_business_assistant_prefix(content, profile)`.
- Use DB profile prefix for the dialog.
- Apply prefix to:
  - auto/direct replies,
  - approval-send replies,
  - mention-direct replies.
- Avoid double-prefix if content already starts with configured prefix.
- Preserve Telegram message length limits after prefix.

Scope / likely files:
- `gateway/platforms/telegram.py`
- `gateway/platforms/telegram_business_profiles.py`
- `tests/gateway/test_telegram_business.py`

Acceptance criteria:
- Default prefix is `🤖 Hermes:`.
- Per-dialog prefix from DB is used.
- Prefix is not duplicated.
- Empty prefix disables visible prefix if owner explicitly configures it.
- Prefix works for both direct auto-send and approval-send.

Evidence route:
- Existing automated checks first: Business direct/approval send tests.
- Add tests with fake bot send capture and in-memory profile DB.
- Bounded acceptance probe: call send helpers with configured profile.
- Access/runtime needed: container test runner only.
- Outcome boundary: proves outgoing text formatting; does not prove Telegram rendering.

Test plan:
- Positive:
  - `test_business_auto_send_applies_database_prefix`
  - `test_business_approval_send_applies_database_prefix`
- Negative:
  - `test_business_send_does_not_double_prefix`
- Edge cases:
  - long first chunk with prefix
  - empty configured prefix

Dependencies:
- Depends on: Task 1.
- Blocks: final integration task.
- Can run parallel with: Tasks 2, 3, 4.

Executor:
- `aad-implementer`.

---

### Task 6: Explicit safe invocation policy

Goal:
- Let configured Business dialogs invoke Hermes with a mention/wake phrase without enabling unsafe slash commands.

Boundary:
- System area: Telegram Business ingress/mode routing.
- Primary verification: `tests/gateway/test_telegram_business.py`.

Existing pattern / reuse:
- Business mode handling (`ignored`, `watch`, `draft`, `auto`).
- Current enqueue path for mode/draft/latest-message.
- Bot username metadata available from Telegram bot/application where possible.

Missing change:
- Add mention detection for configured bot username, e.g. `@HermesBot ...`.
- Read `invocation_policy` from DB profile:
  - `off`: no special trigger.
  - `mention_draft`: enqueue as draft/approval.
  - `mention_direct`: enqueue/send directly once.
- Strip mention marker from model-visible current message or wrap it as an explicit assistant invocation, without passing `/commands` to slash dispatch.
- Keep `/restart@BotName`, `/new`, etc. blocked as Hermes commands.

Scope / likely files:
- `gateway/platforms/telegram.py`
- `gateway/platforms/telegram_business_profiles.py`
- `tests/gateway/test_telegram_business.py`

Acceptance criteria:
- With `off`, mention does not override chat mode.
- With `mention_draft`, mention queues approval-safe draft.
- With `mention_direct`, mention sends direct response if reply permission allows.
- Mention path does not execute gateway slash commands.
- Normal mode behavior remains unchanged for non-mention customer messages.

Evidence route:
- Existing automated checks first: Business mode enqueue tests.
- Add tests with profile DB policy and fake enqueue/send capture.
- Bounded acceptance probe: fake Business update text with `@BotName`.
- Access/runtime needed: container test runner only.
- Outcome boundary: proves routing decisions; not a live Telegram Bot API test.

Test plan:
- Positive:
  - mention_direct sends direct when can_reply true.
  - mention_draft creates draft/approval.
- Negative:
  - mention ignored when policy off.
  - slash command with mention does not dispatch slash command.
- Edge cases:
  - case-insensitive username match
  - mention with punctuation/newline
  - no known bot username fallback disabled or uses configured alias only

Dependencies:
- Depends on: Task 1 and Task 4.
- Blocks: final integration task.
- Can run parallel with: Task 7/8 after API contracts settle.

Executor:
- `aad-implementer`.

---

### Task 7: Telegram bot inline buttons for prompt/settings

Goal:
- Add owner/admin Telegram bot controls to view/edit/clear per-dialog prompt/settings from inline buttons.

Boundary:
- System area: Telegram owner control panel callbacks.
- Primary verification: `tests/gateway/test_telegram_business.py` callback tests.

Existing pattern / reuse:
- `_business_mode_keyboard()` existing buttons.
- Existing `bm:r:<token>` Add rule flow:
  - pending token stored per owner/chat/thread,
  - next owner text consumed by `_maybe_handle_business_rule_text()`.
- Existing callback authorization via `_is_callback_user_authorized()`.

Missing change:
- Add buttons:
  - `🧠 Prompt` -> `bm:p:<token>` starts prompt edit flow.
  - `🧹 Clear prompt` -> `bm:pc:<token>` clears prompt.
  - Optional later: prefix/policy buttons; keep first implementation prompt-focused unless scope allows.
- Add pending prompt token map, analogous to `_business_pending_rule_tokens`.
- Add `_maybe_handle_business_prompt_text(message)` before normal owner message handling.
- On next owner text, save `dialog_prompt` through DB profile store.
- `/cancel` cancels prompt edit.
- Record `settings_changed` history event.

Scope / likely files:
- `gateway/platforms/telegram.py`
- `gateway/platforms/telegram_business_profiles.py`
- `tests/gateway/test_telegram_business.py`

Acceptance criteria:
- Business card keyboard includes prompt edit button.
- Prompt callback is owner/admin-authorized only.
- Next owner text is consumed and saved to DB as dialog prompt.
- `/cancel` cancels without saving.
- Clear prompt writes empty prompt to DB.
- Existing Add rule flow still works.

Evidence route:
- Existing automated checks first: callback/mode/rule tests.
- Add tests around callback data and pending-prompt flow.
- Bounded acceptance probe: fake callback query + fake next owner message.
- Access/runtime needed: container test runner only.
- Outcome boundary: proves bot-button flow; not live Telegram UI rendering.

Test plan:
- Positive:
  - `test_business_keyboard_contains_prompt_button`
  - `test_business_prompt_callback_consumes_next_owner_text_into_database`
  - `test_business_clear_prompt_callback_clears_database_prompt`
- Negative:
  - unauthorized callback rejected.
  - `/cancel` does not save prompt.
- Edge cases:
  - long prompt rejected or normalized per store policy.
  - prompt edit in owner topic respects thread key.

Dependencies:
- Depends on: Tasks 1 and 2 history event convention.
- Blocks: final integration task.
- Can run parallel with: Task 8 after API types settle.

Executor:
- `aad-implementer`.

---

### Task 8: Dashboard settings UI and BFF routes

Goal:
- Add dashboard/admin UI for per-dialog prompt/settings and route through backend settings API.

Boundary:
- System area: Next dashboard frontend/BFF.
- Primary verification: dashboard unit/component/API tests.

Existing pattern / reuse:
- `apps/telegram-business-dashboard/src/lib/business/api.ts` client pattern.
- Existing BFF route files under `src/app/api/business/chats/[token]/...`.
- Existing `ChatDetailView` cards and UI primitives.
- Existing tests:
  - `src/lib/business/business-api.test.ts`
  - `src/app/api/business/route-handlers.test.ts`
  - `src/components/business/business-dashboard-ui.test.tsx`

Missing change:
- Add types:
  - `BusinessInvocationPolicy`
  - `BusinessDialogSettings`
  - `BusinessSettingsResponse`
- Add client functions:
  - `fetchBusinessChatSettings(token, initData)`
  - `updateBusinessChatSettings(token, initData, settingsPatch)`
- Add BFF route:
  - `apps/telegram-business-dashboard/src/app/api/business/chats/[token]/settings/route.ts`
- Add settings section in chat detail UI:
  - assistant name,
  - assistant prefix,
  - dialog prompt textarea,
  - dialog notes textarea,
  - invocation policy selector,
  - save/clear/reset states.

Scope / likely files:
- `apps/telegram-business-dashboard/src/lib/business/types.ts`
- `apps/telegram-business-dashboard/src/lib/business/api.ts`
- `apps/telegram-business-dashboard/src/components/business/chat-detail-view.tsx`
- `apps/telegram-business-dashboard/src/components/business/chat-detail-shell.tsx`
- `apps/telegram-business-dashboard/src/app/api/business/chats/[token]/settings/route.ts`
- `apps/telegram-business-dashboard/src/**/*test.ts(x)`

Acceptance criteria:
- Dashboard loads settings for selected chat.
- Owner can edit and save dialog prompt/settings.
- Save calls PATCH settings route and updates visible state.
- Clear prompt is available and works.
- Validation/backend errors render non-destructively.
- Unauthorized still shows existing Telegram-launch auth UX.
- Existing mode/draft controls still work.

Evidence route:
- Existing automated checks first: frontend tests.
- Add tests for API client, BFF route, and component interactions.
- Bounded acceptance probe: component render with fake data and simulated save.
- Access/runtime needed: containerized dashboard test/typecheck; no host npm.
- Outcome boundary: proves frontend contract and state behavior; not live Telegram WebApp.

Test plan:
- Positive:
  - API client sends PATCH body.
  - BFF route forwards GET/PATCH with auth headers.
  - UI shows current prompt and saves changed prompt.
- Negative:
  - API error displays alert.
  - unauthorized route maps to auth state.
- Edge cases:
  - empty prompt
  - emoji prefix
  - mobile/narrow layout remains usable via existing component snapshots/queries where practical.

Dependencies:
- Depends on: Task 2.
- Blocks: final integration task.
- Can run parallel with: Tasks 5/6/7.

Executor:
- `aad-implementer` with frontend/UI focus.

---

### Task 9: Runtime profile lookup and cache invalidation correctness

Goal:
- Ensure runtime reads current dialog settings from DB when building Business prompt/send behavior and updates cached agent context correctly when settings change.

Boundary:
- System area: gateway runtime integration.
- Primary verification: gateway tests around agent cache/signature/session context.

Existing pattern / reuse:
- Existing `ephemeral_system_prompt` / `channel_prompt` cache signature behavior in `gateway/run.py`.
- Existing event metadata/channel context patterns.

Missing change:
- Add a consistent place to attach DB profile settings to Business `MessageEvent` metadata/channel context before agent creation.
- Ensure settings changes cause a new effective prompt/cache signature for the affected dialog only.
- Do not reload global toolsets or mutate past transcript.

Scope / likely files:
- `gateway/platforms/telegram.py`
- `gateway/run.py`
- `gateway/session.py`
- `tests/gateway/test_telegram_business.py`
- `tests/gateway/test_session.py`

Acceptance criteria:
- Business event for token A receives token A DB profile.
- Changing token A prompt changes token A effective prompt.
- Token B prompt remains unaffected.
- Prompt changes do not corrupt historical transcript or global prompt for other sessions.

Evidence route:
- Existing automated checks first: session prompt tests.
- Add focused tests around two dialogs and settings update.
- Bounded acceptance probe: build/run gateway agent context with fake profile store.
- Access/runtime needed: container test runner only.
- Outcome boundary: proves prompt/profile routing; not full LLM response quality.

Test plan:
- Positive:
  - `test_business_runtime_reads_current_profile_from_database`
  - `test_business_profile_change_affects_only_matching_dialog_prompt`
- Negative:
  - missing profile falls back to defaults.
- Edge cases:
  - settings update while session exists.

Dependencies:
- Depends on: Tasks 1 and 3; easier after Task 2.
- Blocks: final integration task.
- Can run parallel with: UI tasks after contracts settle.

Executor:
- `aad-implementer`.

---

### Task 10: Auto/draft/direct behavior cleanup and evidence

Goal:
- Make Business reply modes and explicit invocation behavior clear, testable, and documented in code/API responses.

Boundary:
- System area: Telegram Business mode routing and dashboard responses.
- Primary verification: mode/direct/draft gateway tests and dashboard API tests.

Existing pattern / reuse:
- Existing modes `ignored`, `watch`, `draft`, `auto`.
- Existing `request_draft()` dashboard API deliberately draft-only.
- Existing `_maybe_enqueue_business_mode_event()`.

Missing change:
- Keep dashboard `Generate draft` approval-safe and never direct-send.
- Ensure `auto` mode direct-sends when `can_reply` allows.
- Ensure `mention_direct` direct-sends as one-shot only when policy allows.
- If `can_reply=false`, fail closed and notify owner/history with a clear failure status.

Scope / likely files:
- `gateway/platforms/telegram.py`
- `gateway/platforms/telegram_business_dashboard_api.py`
- `tests/gateway/test_telegram_business.py`
- `tests/gateway/test_telegram_business_dashboard_api.py`

Acceptance criteria:
- `watch`: notify/watch only.
- `draft`: approval draft only.
- `auto`: direct send only when can_reply.
- dashboard draft request remains `sentToCustomer: false`.
- mention_direct does not change persistent mode.
- direct-send failure due to permissions is visible to owner/history.

Evidence route:
- Existing automated checks first: current mode tests.
- Add/extend tests around reply permission and one-shot invocation mode.
- Bounded acceptance probe: fake bot/direct-send permission responses.
- Access/runtime needed: container test runner only.
- Outcome boundary: proves app routing; not live Telegram permission behavior beyond mocked API contracts.

Test plan:
- Positive:
  - auto direct-send path emits prefixed message.
  - dashboard draft stays approval-safe.
- Negative:
  - can_reply false blocks direct send and records failure.
- Edge cases:
  - mode switch to auto enqueues latest message once.
  - mention_direct in draft mode does not persist mode auto.

Dependencies:
- Depends on: Tasks 5 and 6.
- Blocks: final integration task.
- Can run parallel with: Task 8 after core routing tests pass.

Executor:
- `aad-implementer`.

---

### Task 11: Documentation/config surface

Goal:
- Document Business dialog profiles, DB-backed settings, prompt safety, modes, invocation policy, and prefix behavior.

Boundary:
- System area: developer/user docs and config comments.
- Primary verification: docs review plus no broken references in tests where docs snippets are asserted.

Existing pattern / reuse:
- Existing gateway/dashboard docs if present.
- Existing README/website style.

Missing change:
- Add concise docs for:
  - what Business dialog profiles are,
  - settings stored in DB,
  - dashboard and bot-button editing paths,
  - command safety invariants,
  - modes and invocation policies,
  - prefix behavior.

Scope / likely files:
- `website/docs/...` or existing Telegram/gateway docs path after discovery.
- Possibly `AGENTS.md` if new implementation pitfall is important.
- This task package final report.

Acceptance criteria:
- Docs explain settings source of truth is DB.
- Docs explain Business customer slash commands are not Hermes commands.
- Docs explain owner manual messages are context.
- Docs explain how to edit prompt in dashboard and bot buttons.

Evidence route:
- Existing automated checks first: none unless docs tests exist.
- Bounded acceptance probe: static read of docs by owner.
- Access/runtime needed: none beyond repo.
- Outcome boundary: docs accuracy only.

Test plan:
- Manual:
  - owner reads docs and confirms behavior matches implementation.

Dependencies:
- Depends on: final API/UX names from Tasks 2, 7, 8.
- Blocks: final acceptance package.
- Can run parallel with: final verification once names stable.

Executor:
- `aad-implementer` or owner direct.

---

### Task 12: Final integration and container-only verification

Goal:
- Prove the end-to-end behavior with targeted tests and container-only checks.

Boundary:
- System area: integration acceptance.
- Primary verification: targeted Python gateway tests + dashboard tests/typecheck in containers.

Existing pattern / reuse:
- Repo instruction: use `scripts/run_tests.sh`, and for this user/task run tests in containers only.
- Existing Docker test scripts:
  - `scripts/run_tests_docker.sh`
  - `docker-compose.test.yml` build-assets path where needed.

Acceptance scenario:
1. A Business chat profile is stored in DB with:
   - prompt: `Это моя подруга. Отвечай тепло, с юмором.`
   - prefix: `🤖 Hermes:`
   - invocation policy: `mention_direct`.
2. Session prompt has owner/contact/Hermes roles and includes this profile.
3. Customer sends normal message; mode behavior is respected.
4. Owner sends manual message; it is recorded as owner context, not customer request.
5. Customer sends next message; prompt/context includes owner message.
6. Customer `/restart` does not dispatch command.
7. Customer `@HermesBot ...` triggers configured invocation behavior.
8. Hermes outgoing message is prefixed.
9. Dashboard and Telegram bot prompt editing both update the same DB-backed setting.

Evidence route:
- Existing automated checks first: all targeted tests from tasks.
- Add an integration test if smaller tests leave gaps.
- Commands must run in containers only; do not run host pytest/npm/uv.
- Suggested local container commands to adapt to repo state:
  - `HERMES_TEST_WORKERS=4 scripts/run_tests_docker.sh tests/gateway/test_telegram_business_profiles.py tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_business.py tests/gateway/test_session.py`
  - dashboard tests/typecheck via existing Docker compose service, not host npm.
- Outcome boundary: container tests prove local simulated gateway/dashboard behavior; live Telegram API smoke remains manual/prod-only.

Dependencies:
- Depends on: Tasks 1-11.
- Blocks: prod rollout.
- Can run parallel with: none.

Executor:
- root/slice owner.

## Dependency graph

Recommended waves:

1. Task 1 — DB store.
2. Parallel after Task 1:
   - Task 2 — backend API,
   - Task 3 — prompt integration,
   - Task 4 — command safety,
   - Task 5 — prefix.
3. Parallel after core contracts:
   - Task 6 — invocation policy,
   - Task 7 — Telegram bot prompt buttons,
   - Task 8 — dashboard settings UI,
   - Task 9 — runtime profile/cache integration.
4. Task 10 — mode/direct cleanup.
5. Task 11 — docs.
6. Task 12 — final integration/container verification.

## Do-not-touch / guardrails

- Do not treat customer text as system prompt.
- Do not let Business customer slash commands reach Hermes command dispatch.
- Do not break normal Telegram DM slash commands.
- Do not break owner `/business` control panel.
- Do not change global prompt/toolsets mid-conversation outside existing cache-aware prompt mechanisms.
- Do not store secrets or private credentials in profile settings/history.
- Do not use host pytest/npm/uv/build commands for verification; container-only for this task.
- Rebase is not required unless a later owner explicitly chooses it.

## Initial acceptance checklist

- [ ] DB store exists and has in-memory tests.
- [ ] Dashboard backend GET/PATCH settings uses DB store.
- [ ] Dashboard UI edits settings.
- [ ] Telegram bot buttons edit/clear prompt.
- [ ] Business prompt frames owner/contact/Hermes roles.
- [ ] DB prompt/settings are injected into the right dialog only.
- [ ] Customer slash commands are blocked at adapter and gateway layers.
- [ ] Prefix is applied to Hermes Business sends.
- [ ] Mention invocation policy works and does not open slash-command execution.
- [ ] Mode/direct/draft behavior is clear and tested.
- [ ] Container-only targeted verification is recorded under `verification/`.
