PI_RESULT: PASS
TASK: Telegram Business dashboard 24-hour session lease
TASK_PACKAGE: docs/plans/2026-05-26-telegram-business-media
REPORT_PATH: docs/plans/2026-05-26-telegram-business-media/reports/aad-implementer-dashboard-session-lease.md
PROGRESS_PATH: docs/plans/2026-05-26-telegram-business-media/progress/aad-implementer-dashboard-session-lease.md
COMMITS:
- 3011c9568: feat: add Telegram dashboard session lease
FILES_CHANGED:
- apps/telegram-business-dashboard/src/lib/server/telegram-auth.ts: added server-only 24-hour HMAC-signed dashboard session cookie issuing/validation helpers using TELEGRAM_BOT_TOKEN and admin allowlist re-checks.
- apps/telegram-business-dashboard/src/lib/server/business-route.ts: kept initData authoritative, added cookie fallback auth, centralized auth error mapping, and response cookie refresh helper for fresh initData requests.
- apps/telegram-business-dashboard/src/app/api/session/route.ts: sets HttpOnly Secure SameSite=None 24-hour dashboard session cookie on successful fresh initData validation.
- apps/telegram-business-dashboard/src/app/api/business/chats/route.ts: attaches refreshed dashboard cookie when authenticated with fresh initData.
- apps/telegram-business-dashboard/src/app/api/business/chats/[token]/route.ts: attaches refreshed dashboard cookie when authenticated with fresh initData.
- apps/telegram-business-dashboard/src/app/api/business/chats/[token]/history/route.ts: attaches refreshed dashboard cookie when authenticated with fresh initData.
- apps/telegram-business-dashboard/src/app/api/business/chats/[token]/mode/route.ts: attaches refreshed dashboard cookie when authenticated with fresh initData.
- apps/telegram-business-dashboard/src/app/api/business/chats/[token]/draft/route.ts: attaches refreshed dashboard cookie when authenticated with fresh initData.
- apps/telegram-business-dashboard/src/app/api/session/route.test.ts: added Set-Cookie assertions for valid POST /api/session.
- apps/telegram-business-dashboard/src/app/api/business/route-handlers.test.ts: added cookie-only proxy, fresh-cookie refresh, tampered/expired/malformed cookie rejection coverage.
- docs/plans/2026-05-26-telegram-business-media/progress/aad-implementer-dashboard-session-lease.md: implementation progress and check notes.
AC_VERIFICATION:
- Valid fresh initData still returns `{ ok: true, user }` and includes signed session Set-Cookie with HttpOnly, Secure, Path, 24-hour Max-Age/Expires, SameSite=None: `npm run test:auth -- src/app/api/session/route.test.ts src/app/api/business/route-handlers.test.ts src/lib/server/telegram-auth.test.ts` passed; `route.test.ts` asserts response body/status and cookie flags — passed.
- Invalid signature, stale initData (>5 min), non-admin, and missing config still reject as before: same targeted auth test command passed existing invalid signature, expired auth_date, non-admin, and missing TELEGRAM_BOT_TOKEN cases — passed.
- Business route with cookie and no initData proxies to Hermes with actor user id: same targeted auth test command passed new cookie-only GET /api/business/chats test asserting one fetch and `x-telegram-user-id` — passed.
- Expired/tampered/malformed cookie rejects without calling Hermes: same targeted auth test command passed new tampered, expired, and malformed cookie tests asserting 401 and `fetch` not called — passed.
- Fresh initData Business request still proxies as before and may set/refresh cookie: same targeted auth test command passed existing fresh initData proxy tests and new Set-Cookie assertion on GET /api/business/chats — passed.
- Service token remains server-only: same targeted auth test command passed existing `HERMES_DASHBOARD_API_TOKEN` client-exposure regression test; implementation did not touch `hermes-dashboard-api.ts` or introduce NEXT_PUBLIC token vars — passed.
TESTS_RUN:
- RED: `cd apps/telegram-business-dashboard && npm run test:auth -- src/app/api/session/route.test.ts src/app/api/business/route-handlers.test.ts src/lib/server/telegram-auth.test.ts`: failed as expected before implementation (missing Set-Cookie; `issueDashboardSessionCookie is not a function`) — expected failure captured.
- GREEN/final: `cd apps/telegram-business-dashboard && npm run test:auth -- src/app/api/session/route.test.ts src/app/api/business/route-handlers.test.ts src/lib/server/telegram-auth.test.ts`: 3 files passed, 27 tests passed — passed.
QUALITY_CHECKS:
- `cd apps/telegram-business-dashboard && npm run typecheck`: initially failed on optional payload narrowing in `telegram-auth.ts`, fixed; final run passed — passed.
- `cd apps/telegram-business-dashboard && npm run lint`: passed — passed.
- `git diff --check`: no whitespace errors — passed.
QUALITY_NOTES:
- Readability/reuse: reused existing `validateTelegramAdminInitData()`, `TelegramAdminAuthError`, central `authenticateTelegramAdmin()`, and Business route proxy helpers; extracted shared cookie option helper to avoid duplicating flags/lifetime.
- Error handling/logging: preserved existing public error shapes (`missing_init_data`, `unauthorized`, `forbidden`, `auth_not_configured`) and added no new logging.
- Backend/API/data: route methods/status/body shapes are preserved; cookie fallback only changes auth gate behavior and continues stripping `initData` from upstream POST bodies.
- Frontend/UI: not relevant; no client/UI files changed.
- DevOps/runtime: no new env vars; signing uses existing server-only `TELEGRAM_BOT_TOKEN`; `HERMES_DASHBOARD_API_TOKEN` behavior unchanged.
- Security: cookie is signed with server-side HMAC, HttpOnly, Secure, SameSite=None, Path=/, Max-Age/Expires 24h; fresh initData remains 5-minute authoritative path; admin allowlist is re-checked on cookie validation; service token and bot token are not exposed to client code.
- Concurrency/idempotency: auth is stateless and safe to retry; fresh initData refreshes the same lease type without server persistence.
- Compatibility/performance: no external calls added; cookie validation is bounded JSON/HMAC work; existing missing-initData response is preserved when neither initData nor cookie is present.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: Owner pre-existing dirty task-package files remained unstaged (`docs/plans/2026-05-26-telegram-business-media/plan.md`, `progress/slice-owner.md`) and were not modified by this implementer.
NOTES: Implementation evidence only; slice owner/auditor should make the acceptance decision. No deploy, push, PR, or client UI changes performed.
