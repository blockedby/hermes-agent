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
- Valid fresh initData still returns `{ ok: true, user }` and includes signed session Set-Cookie with HttpOnly, Secure, Path, 24-hour Max-Age/Expires, SameSite=None: targeted auth tests passed.
- Invalid signature, stale initData (>5 min), non-admin, and missing config still reject as before: targeted auth tests passed existing regressions.
- Business route with cookie and no initData proxies to Hermes with actor user id: targeted auth tests passed new cookie-only GET /api/business/chats coverage.
- Expired/tampered/malformed cookie rejects without calling Hermes: targeted auth tests passed new negative cookie coverage.
- Fresh initData Business request still proxies as before and may set/refresh cookie: targeted auth tests passed existing proxy coverage plus new Set-Cookie assertion.
- Service token remains server-only: existing exposure regression test passed; no `NEXT_PUBLIC_HERMES_DASHBOARD_API_TOKEN` introduced.
TESTS_RUN:
- RED: `cd apps/telegram-business-dashboard && npm run test:auth -- src/app/api/session/route.test.ts src/app/api/business/route-handlers.test.ts src/lib/server/telegram-auth.test.ts`: failed as expected before implementation (missing Set-Cookie; `issueDashboardSessionCookie is not a function`).
- GREEN/final: `cd apps/telegram-business-dashboard && npm run test:auth -- src/app/api/session/route.test.ts src/app/api/business/route-handlers.test.ts src/lib/server/telegram-auth.test.ts`: 3 files passed, 27 tests passed.
QUALITY_CHECKS:
- `cd apps/telegram-business-dashboard && npm run typecheck`: final run passed.
- `cd apps/telegram-business-dashboard && npm run lint`: passed.
- `git diff --check`: passed.
QUALITY_NOTES:
- Reused existing server auth/BFF patterns and kept tokens server-only.
- Added no logs and no client/UI changes.
- Stateless signed cookie validation re-checks expiry, signature shape, and admin allowlist before proxying.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: pre-existing owner task-package dirty files (`plan.md`, `progress/slice-owner.md`) were left unstaged/unmodified by this implementer.
NOTES: No deploy, push, PR, or broader Telegram media changes performed.
