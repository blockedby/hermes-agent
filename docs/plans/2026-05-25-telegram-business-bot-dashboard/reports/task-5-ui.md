PI_RESULT: PASS
TASK: Task 5 — Dashboard UI list/detail/actions
TASK_PACKAGE: docs/plans/2026-05-25-telegram-business-bot-dashboard
REPORT_PATH: docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/task-5-ui.md
PROGRESS_PATH: not provided
COMMITS:
- d0808d9d2: feat: add telegram business dashboard UI
FILES_CHANGED:
- apps/telegram-business-dashboard/src/app/page.tsx: Replaced the setup shell with the Business dashboard client shell.
- apps/telegram-business-dashboard/src/app/chats/[token]/page.tsx: Added chat detail route wired to the detail shell.
- apps/telegram-business-dashboard/src/components/business/dashboard-shell.tsx: Added Telegram-initData-aware chat list data loading, refresh, search, and filter state.
- apps/telegram-business-dashboard/src/components/business/dashboard-view.tsx: Added mobile-first header/refresh, count cards, filter chips, search, chat cards, and loading/empty/error/unauthorized states.
- apps/telegram-business-dashboard/src/components/business/chat-detail-shell.tsx: Added detail/history loading plus mode and draft action handlers against Task 4 BFF routes.
- apps/telegram-business-dashboard/src/components/business/chat-detail-view.tsx: Added detail status sections, mode controls, Generate draft now action, latest preview, and history timeline.
- apps/telegram-business-dashboard/src/lib/business/types.ts: Moved shared Business dashboard response types out of server-only code for client reuse.
- apps/telegram-business-dashboard/src/lib/business/api.ts: Added small client BFF fetch helpers that pass Telegram initData via headers and map UI-safe errors.
- apps/telegram-business-dashboard/src/lib/business/view-model.ts: Added count/filter/relative-time/display helpers.
- apps/telegram-business-dashboard/src/lib/server/hermes-dashboard-api.ts: Re-exported shared Business dashboard types while preserving server-only Hermes API client behavior.
- apps/telegram-business-dashboard/src/lib/telegram/use-telegram-webapp.ts: Applied Telegram color scheme/theme params when available while preserving outside-Telegram missing state.
- apps/telegram-business-dashboard/src/components/business/business-dashboard-ui.test.tsx: Added server-rendered UI/component tests for list/detail/states and helper behavior.
- apps/telegram-business-dashboard/src/lib/business/business-api.test.ts: Added mocked client API tests for GET/POST route calls and error mapping.
- apps/telegram-business-dashboard/vitest.config.mts: Included `.test.tsx` files so focused UI tests run under the existing Vitest setup.
AC_VERIFICATION:
- Owner can see chat list and mode counts: `business-dashboard-ui.test.tsx` renders count cards, mode badges, chat cards, pending/failed indicators, and preview text with mocked chats — passed.
- Owner can open chat detail: `/chats/[token]` route added and production build route table lists `/chats/[token]` — passed.
- Owner can change mode with visible confirmation: `ChatDetailShell` POSTs to `/api/business/chats/{token}/mode`, updates chat state, and `ChatDetailView` renders ignored/watch/draft/auto controls plus action status — passed by typecheck/build and component/API tests.
- Owner can request draft generation with visible queued state: `ChatDetailShell` POSTs to `/draft` with `{ source: "latest" }`; detail UI renders `Generate draft now` and success/error/queued status copy; `business-api.test.ts` asserts BFF call shape — passed.
- UI handles loading/empty/error/unauthorized states: `business-dashboard-ui.test.tsx` renders loading skeleton, empty copy, retryable error, and Open-from-Telegram/unauthorized copy — passed.
- Mobile viewport has no horizontal overflow: implemented one-column max-width layout, `min-w-0`/`truncate`/`break-words`, and horizontally scrollable filter chips; production HTTP smoke loaded `/` and `/chats/smoke-token` at 200 — passed as implementation smoke, no screenshot captured.
TESTS_RUN:
- `cd apps/telegram-business-dashboard && npm run test:auth -- src/components/business/business-dashboard-ui.test.tsx src/lib/business/business-api.test.ts`: RED failed before implementation with missing `./api`; GREEN passed, 2 files / 7 tests.
- `cd apps/telegram-business-dashboard && npm run test:auth`: passed, 5 files / 29 tests.
- `cd apps/telegram-business-dashboard && npm run lint`: passed.
- `cd apps/telegram-business-dashboard && npm run typecheck`: passed.
- `cd apps/telegram-business-dashboard && npm run build`: passed; Next route table includes `/`, Business API routes, `/api/session`, and `/chats/[token]`.
- `cd apps/telegram-business-dashboard && (npm run start ... curl / and /chats/smoke-token ...)`: passed; root=200, detail=200, root title found.
- `git diff --check`: passed.
QUALITY_CHECKS:
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `npm run build`: passed.
- `npm run test:auth`: passed, including mocked UI/API tests.
- Production HTTP smoke with `npm run start` + `curl`: passed for `/` and `/chats/smoke-token`; browser automation/screenshot was not available in this tool environment.
QUALITY_NOTES:
- Readability/reuse: Reused existing shadcn/ui primitives, lucide icons, Telegram hook, and Task 4 BFF routes; kept state local in two small shells with pure presentational views and helpers.
- Error handling/logging: No new logging; client maps BFF errors to stable UI-safe codes and preserves retry paths.
- Backend/API/data: No backend persistence/API changes; client calls existing BFF routes only and does not bypass Task 4 server-side auth.
- Frontend/UI: Mobile-first max-width layout, sticky header/refresh, count cards/chips, search/filter controls, card list, detail route, a11y labels/roles, loading/empty/error/unauthorized states, and long-text wrapping/truncation implemented.
- DevOps/runtime: No env, dependency, or deployment changes; Vitest include widened to `.test.tsx` without adding packages.
- Security: Telegram initData is sent only to app BFF routes; Hermes service token remains server-only; Generate draft now copy and call path explicitly avoid direct customer sends.
- Concurrency/idempotency: UI performs one request per action and delegates mode/draft idempotency to the Hermes dashboard API; no retries added.
- Compatibility/performance: No heavy global state library; local filtering avoids extra BFF calls while keeping chat list bounded by existing API behavior; build remains static for shell routes with dynamic API routes.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: Add screenshot-based Telegram mobile visual evidence when browser automation or a deployed preview is available.
NOTES: Did not push. This report records implementation evidence only; owner/auditor retain acceptance decision.
