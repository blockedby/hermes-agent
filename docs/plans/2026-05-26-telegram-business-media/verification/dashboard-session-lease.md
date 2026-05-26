# Verification: Telegram Business dashboard session lease

Date: 2026-05-26
Worktree: `/home/kcnc/code/hermes/hermes-agent`

## Acceptance verification

- AC1: `POST /api/session` validates fresh Telegram WebApp initData and issues an HttpOnly Secure 24-hour signed cookie.
  - Covered by: `src/app/api/session/route.test.ts`.
  - Result: passed.
  - Evidence: targeted test command below passed; test asserts status/body plus `Set-Cookie` flags/lifetime.

- AC2: Fresh initData invalid signature, >5-minute stale auth_date, non-admin user, and missing config reject as before.
  - Covered by: `src/app/api/session/route.test.ts` and `src/lib/server/telegram-auth.test.ts`.
  - Result: passed.

- AC3: Business BFF route accepts valid cookie without initData and proxies with actor user id.
  - Covered by: `src/app/api/business/route-handlers.test.ts`.
  - Result: passed.

- AC4: Expired, tampered, and malformed cookies reject without calling Hermes.
  - Covered by: `src/app/api/business/route-handlers.test.ts`.
  - Result: passed.

- AC5: Service token remains server-only.
  - Covered by: existing client-exposure regression in `src/app/api/business/route-handlers.test.ts`.
  - Result: passed.

## Fresh command evidence

```text
$ cd apps/telegram-business-dashboard && npm run test:auth -- src/app/api/session/route.test.ts src/app/api/business/route-handlers.test.ts src/lib/server/telegram-auth.test.ts && npm run typecheck && npm run lint

Test Files  3 passed (3)
Tests  27 passed (27)
...
> telegram-business-dashboard@0.1.0 typecheck
> tsc --noEmit

> telegram-business-dashboard@0.1.0 lint
> eslint
```
