PI_RESULT: PASS
TASK: Telegram Business dialog profiles — Task 8 dashboard settings UI
TASK_PACKAGE: docs/plans/2026-06-09-telegram-business-dialog-profiles
REPORT_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task8-dashboard-settings-ui.md
PROGRESS_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task8-dashboard-settings-ui.md
COMMITS:
- e5a85b396: feat(dashboard): add business dialog settings UI
FILES_CHANGED:
- apps/telegram-business-dashboard/src/components/business/chat-detail-shell.tsx: loads settings with selected chat detail/history, preserves detail on settings-only failures, saves settings through existing API client, and manages local clear/reset/dirty state.
- apps/telegram-business-dashboard/src/components/business/chat-detail-view.tsx: adds compact Dialog settings card for assistantDisplayName, assistantPrefix, dialogPrompt, dialogNotes, invocationPolicy, save/clear/reset controls, and non-destructive status alerts.
- apps/telegram-business-dashboard/src/components/business/business-dashboard-ui.test.tsx: adds component/shell coverage for settings visibility, save route wiring, clear/reset helpers, non-destructive errors, and existing mode/draft controls; includes scoped Base UI test mocks to avoid the pre-existing SSR invalid-hook-call baseline.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task8-dashboard-settings-ui.md: implementation progress and verification notes.
AC_VERIFICATION:
- Dashboard loads settings for selected chat: `fetchChatDetailSnapshot("tok-watch", "init-data")` component/shell test asserts `fetchBusinessChatSettings` is called with the selected token/initData and returns settings alongside chat/history — passed.
- Owner can edit assistantDisplayName, assistantPrefix, dialogPrompt, dialogNotes, invocationPolicy: static component test renders labeled controls with changed draft values for all fields; shell exposes patch handler for those fields — passed.
- Save calls PATCH settings route and updates visible state: `saveBusinessChatSettingsSnapshot` test asserts `updateBusinessChatSettings("tok-watch", "init-data", changedSettings)` and returns saved settings; shell applies returned settings to saved/draft state — passed.
- Clear prompt is available and works without clearing all settings: component test asserts Clear prompt button is visible; helper test asserts clear changes only `dialogPrompt` and preserves `dialogNotes`/other fields — passed.
- Reset/discard state is available for local unsaved edits: component test asserts Reset changes button is visible; helper test asserts reset returns saved settings and dirty-state helper distinguishes changed vs saved — passed.
- Validation/backend errors render non-destructively; current chat detail/mode/draft controls remain usable: component test renders settings load/action errors while also asserting Mode controls, Generate draft now, and Latest preview remain visible — passed.
- Unauthorized still shows existing Telegram-launch auth UX: existing dashboard component test for unauthorized state still passes in full dashboard Vitest — passed.
- Existing mode/draft controls still work: existing detail component assertions for mode buttons and draft generation remain passing; new settings card test also asserts Generate draft now and Optional draft topic remain visible — passed.
TESTS_RUN:
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run test:auth -- src/components/business/business-dashboard-ui.test.tsx`: baseline before test mocks failed with pre-existing Base UI SSR invalid hook call; after RED tests failed as expected for missing Dialog settings UI/helper functions; final GREEN passed, 1 file / 8 tests.
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run test:auth`: passed, 6 files / 46 tests.
QUALITY_CHECKS:
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run typecheck`: passed.
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run lint`: passed.
- `git diff --check`: passed.
QUALITY_NOTES:
- Readability/reuse: Reused existing API client functions, ChatDetailShell refresh/error patterns, and ChatDetailView card/alert/button hierarchy. Exported small shell helpers only because the repo has no DOM testing dependency and the shell state behavior needed automated proof.
- Error handling/logging: Settings-only load/save failures are shown in scoped alerts and do not unmount chat detail; no new logging added.
- Backend/API/data: No backend/Python/storage changes. UI uses existing BFF/client settings contract.
- Frontend/UI: Settings card is below mode controls, uses existing Card/Button/Alert/Skeleton/Badge styling conventions and labeled form controls, preserves single-column mobile layout with `sm:` enhancement, and avoids a second chat surface.
- DevOps/runtime: No env/config/deployment changes.
- Security: No secrets logged; service-token handling remains in existing BFF route/client tests; settings form treats owner input as controlled text and does not use unsafe HTML.
- Concurrency/idempotency: Save is a single PATCH call guarded by loading/dirty state; local clear/reset are deterministic client-state updates.
- Compatibility/performance: Existing detail, mode, draft, auth, API, and route tests remain passing; added settings fetch is scoped to selected chat detail load.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: If richer interaction testing is desired, add a DOM test dependency/environment for the dashboard; current component tests use server rendering and pure shell helpers due existing package constraints.
PARENT_ACTION_REQUIRED:
- Action: none.
- Reason: n/a.
- Expected evidence: n/a.
- Safety bounds: n/a.
NOTES: Browser/screenshot evidence was waived by the delegated visual gate; automated component evidence covers visible settings controls and non-destructive states.
