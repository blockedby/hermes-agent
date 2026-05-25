PI_RESULT: PASS
TASK: Task 4 — Next API proxy/BFF to Hermes VPS API
TASK_PACKAGE: docs/plans/2026-05-25-telegram-business-bot-dashboard
REPORT_PATH: docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/task-4-next-bff.md
PROGRESS_PATH: not provided
COMMITS:
- 5418f2cb2: feat: add telegram business dashboard BFF routes
FILES_CHANGED:
- apps/telegram-business-dashboard/src/lib/server/hermes-dashboard-api.ts: Added typed server-only Hermes Dashboard API fetch client using `HERMES_DASHBOARD_API_BASE_URL` and `HERMES_DASHBOARD_API_TOKEN`, bearer auth, actor header, POST actor body injection, no-store fetches, and JSON response handling.
- apps/telegram-business-dashboard/src/lib/server/business-route.ts: Added shared Telegram admin auth gating, POST JSON parsing, safe upstream error mapping, and initData stripping for proxied POST bodies.
- apps/telegram-business-dashboard/src/app/api/business/chats/route.ts: Added authenticated `GET /api/business/chats` BFF handler.
- apps/telegram-business-dashboard/src/app/api/business/chats/[token]/route.ts: Added authenticated `GET /api/business/chats/[token]` BFF handler.
- apps/telegram-business-dashboard/src/app/api/business/chats/[token]/mode/route.ts: Added authenticated `POST /api/business/chats/[token]/mode` BFF handler.
- apps/telegram-business-dashboard/src/app/api/business/chats/[token]/draft/route.ts: Added authenticated `POST /api/business/chats/[token]/draft` BFF handler.
- apps/telegram-business-dashboard/src/app/api/business/chats/[token]/history/route.ts: Added authenticated `GET /api/business/chats/[token]/history` BFF handler.
- apps/telegram-business-dashboard/src/app/api/business/route-handlers.test.ts: Added mocked-fetch coverage for success, auth rejection, all-route auth gating, actor propagation, safe error mapping, config/network failures, and token exposure guard.
- apps/telegram-business-dashboard/.env.example: Tracked server-only Hermes BFF env placeholders with no secrets.
- apps/telegram-business-dashboard/.gitignore: Allowed `.env.example` to be committed while keeping real env files ignored.
- apps/telegram-business-dashboard/README.md: Documented active server-only Hermes BFF env vars.
AC_VERIFICATION:
- Typed server-only Hermes API client using `HERMES_DASHBOARD_API_BASE_URL` and `HERMES_DASHBOARD_API_TOKEN`: `npm run typecheck` passed; client lives under `src/lib/server/hermes-dashboard-api.ts` and imports `server-only` — passed.
- All BFF routes validate Telegram initData/admin before Hermes calls: `route-handlers.test.ts` includes all five routes missing-initData rejection plus non-admin/invalid-signature checks with `fetch` not called; `npm run test:auth` passed — passed.
- Implemented required routes: Next build route table lists `/api/business/chats`, `/api/business/chats/[token]`, `/draft`, `/history`, `/mode` as dynamic server routes — passed.
- Browser never receives service token: mocked-fetch tests assert no `NEXT_PUBLIC_HERMES_DASHBOARD_API_TOKEN` in `.env.example` and no client-facing source references `HERMES_DASHBOARD_API_TOKEN`; service token is only used in server route/client code — passed.
- Actor user id included for Task 3: tests assert `x-telegram-user-id` on GET/POST and `actorUserId` in POST JSON body while `initData` is not forwarded — passed.
- Hermes 401/403/404/500/errors mapped safely: tests assert upstream 403 becomes `502 dashboard_auth_failed`, 404 becomes `404 not_found`, 500/network becomes `502 dashboard_unavailable`, and missing BFF config becomes `500 dashboard_not_configured` — passed.
- Mocked fetch tests for success and rejection paths: `npm run test:auth` passed with 22 tests across 3 files, including 11 BFF route tests — passed.
TESTS_RUN:
- `cd apps/telegram-business-dashboard && npm run test:auth -- src/app/api/business/route-handlers.test.ts`: RED failed before production code with `Cannot find module './chats/route'`; GREEN passed with 11 tests.
- `cd apps/telegram-business-dashboard && npm run test:auth`: passed, 3 test files / 22 tests.
- `git diff --check`: passed before commit.
QUALITY_CHECKS:
- `cd apps/telegram-business-dashboard && npm run lint`: passed.
- `cd apps/telegram-business-dashboard && npm run typecheck`: passed.
- `cd apps/telegram-business-dashboard && npm run build`: passed; Next route table shows all five Business API routes as dynamic server routes.
QUALITY_NOTES:
- Readability/reuse: Reused existing Task 2 `validateTelegramAdminInitData` helper and kept BFF concerns split between a small route helper and typed Hermes client; no UI or unrelated refactor included.
- Error handling/logging: No new logging; upstream failures are collapsed to stable UI-safe error codes without leaking upstream messages or tokens.
- Backend/API/data: BFF preserves Task 3 endpoint paths and response bodies on success; POST handlers strip browser `initData`, add actor metadata, and let Hermes own mode/draft validation.
- Frontend/UI: No UI implemented, per scope.
- DevOps/runtime: `.env.example`/README now declare server-only `HERMES_DASHBOARD_API_BASE_URL` and `HERMES_DASHBOARD_API_TOKEN`; real env files remain ignored.
- Security: Service bearer token is server-only, never returned to browser, never logged, and never exposed through `NEXT_PUBLIC_*`; all proxy calls require verified Telegram admin first.
- Concurrency/idempotency: BFF does not add persistence or retries; draft/mode write semantics remain delegated to the Task 3 Hermes API.
- Compatibility/performance: Routes use `cache: "no-store"` and dynamic node runtime; no dependency changes; build/typecheck passed.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: Task 5 UI should standardize whether clients pass initData in `x-telegram-init-data` for GETs and either header or body for POSTs; the BFF supports both header and body for POSTs.
NOTES: Report written after implementation commit 5418f2cb2; a follow-up docs-only commit records this report file.
