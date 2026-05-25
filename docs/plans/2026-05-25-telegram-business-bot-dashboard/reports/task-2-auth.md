PI_RESULT: PASS
TASK: Task 2 — Telegram Business Dashboard auth coverage
TASK_PACKAGE: docs/plans/2026-05-25-telegram-business-bot-dashboard
REPORT_PATH: docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/task-2-auth.md
PROGRESS_PATH: docs/plans/2026-05-25-telegram-business-bot-dashboard/progress/aad-implementer-task-2-auth.md
COMMITS:
- 4e7582668: test: cover Telegram dashboard auth
FILES_CHANGED:
- apps/telegram-business-dashboard/package.json: added `test:auth` command and Vitest dev dependency.
- apps/telegram-business-dashboard/package-lock.json: locked Vitest test dependency tree.
- apps/telegram-business-dashboard/vitest.config.mts: configured node test environment, `@` alias, and `server-only` stub for server helper imports.
- apps/telegram-business-dashboard/src/test/server-only-stub.ts: no-op test stub for `server-only` marker package.
- apps/telegram-business-dashboard/src/test/telegram-init-data-fixtures.ts: shared signed Telegram initData fixtures using `@tma.js/init-data-node`.
- apps/telegram-business-dashboard/src/lib/server/telegram-auth.test.ts: helper coverage for valid admin, non-admin, invalid signature, expired auth_date, and missing bot token.
- apps/telegram-business-dashboard/src/app/api/session/route.test.ts: route coverage for 200/403/401/401/500 fail-closed behavior and server-only bot token exposure invariant.
- apps/telegram-business-dashboard/README.md: documented `npm run test:auth`.
- docs/plans/2026-05-25-telegram-business-bot-dashboard/progress/aad-implementer-task-2-auth.md: progress log.
- docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/task-2-auth.md: implementation report.
AC_VERIFICATION:
- Valid admin success: `npm run test:auth` route/helper tests passed; admin signed initData fixture returns helper session and route 200 — passed.
- Valid non-admin 403: `npm run test:auth` route/helper tests passed; signed non-admin fixture fails allowlist and route returns 403 — passed.
- Invalid signature 401: `npm run test:auth` passed; tampered signed fixture maps to route 401 — passed.
- Expired auth_date 401: `npm run test:auth` passed; signed fixture older than the 5 minute helper window maps to route 401 — passed.
- Missing bot token fails closed: `npm run test:auth` passed; helper emits `config_error`, route returns `{ ok: false, error: "auth_not_configured" }` with 500 and no session — passed.
- Bot token not exposed to client: `npm run test:auth` passed; static invariant checks `.env.example` does not define `NEXT_PUBLIC_TELEGRAM_BOT_TOKEN` and client-facing source does not reference `TELEGRAM_BOT_TOKEN` — passed.
TESTS_RUN:
- `cd apps/telegram-business-dashboard && npm run test:auth`: passed (2 test files, 11 tests).
QUALITY_CHECKS:
- `cd apps/telegram-business-dashboard && npm run lint`: passed.
- `cd apps/telegram-business-dashboard && npm run typecheck`: passed.
- `cd apps/telegram-business-dashboard && npm run build`: passed; Next.js 16.2.6 production build completed and `/api/session` remains dynamic node route.
- `cd apps/telegram-business-dashboard && npm audit --omit=dev --audit-level=moderate`: failed; reports existing `next` -> `postcss <8.5.10` moderate advisory, with npm's suggested force fix installing a breaking `next@9.3.3`. Not remediated in this scoped auth-test task.
QUALITY_NOTES:
- Readability/reuse: kept tests focused and extracted shared Telegram initData fixture helpers instead of duplicating fixture signing logic.
- Error handling/logging: preserved existing route/helper error mapping; no logging added.
- Backend/API/data: auth helper and `/api/session` contract are covered without changing response shapes or persistence.
- Frontend/UI: not relevant; no UI behavior changed.
- DevOps/runtime: added dev-only Vitest test dependency and command; README documents the auth test command; Vercel build remains green.
- Security: tests assert invalid/expired/non-admin/missing-token paths deny access and server bot token is not referenced from client-facing source.
- Concurrency/idempotency: not relevant; auth validation is stateless.
- Compatibility/performance: no production runtime dependency or route behavior changes; tests run locally in node environment.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: evaluate the Next/PostCSS moderate audit advisory separately from this task.
NOTES: Initial auth test feedback run failed before final green due to an over-specific invalid-signature error-message assertion; refined to the stable helper contract (`code: unauthorized`).
