## Task
- Mission: Plan and implement a 24-hour server-side session lease for Telegram Business dashboard auth.
- Target: `apps/telegram-business-dashboard` session and Business BFF auth routes.
- Boundaries: No deploy, no push, no PR. No client UI redesign. Keep service token server-only.
- Done when: fresh initData still validates with 5-minute max age; `POST /api/session` issues a 24-hour HttpOnly Secure signed cookie; Business BFF routes accept fresh initData or valid cookie; targeted tests/typecheck/lint pass.

## Context
- Slice model: stayed whole under one slice owner; implementation delegated to one `aad-implementer`.
- Task package: `docs/plans/2026-05-26-telegram-business-media`.
- Implementer report: `reports/aad-implementer-dashboard-session-lease.md`.
- Verification artifact: `verification/dashboard-session-lease.md`.
- Commits created locally: `3011c9568 feat: add Telegram dashboard session lease`, `0f180e6b5 docs: report Telegram dashboard session lease implementation`.

## Changed files
- `apps/telegram-business-dashboard/src/lib/server/telegram-auth.ts`
- `apps/telegram-business-dashboard/src/lib/server/business-route.ts`
- `apps/telegram-business-dashboard/src/app/api/session/route.ts`
- `apps/telegram-business-dashboard/src/app/api/business/chats/route.ts`
- `apps/telegram-business-dashboard/src/app/api/business/chats/[token]/route.ts`
- `apps/telegram-business-dashboard/src/app/api/business/chats/[token]/history/route.ts`
- `apps/telegram-business-dashboard/src/app/api/business/chats/[token]/mode/route.ts`
- `apps/telegram-business-dashboard/src/app/api/business/chats/[token]/draft/route.ts`
- `apps/telegram-business-dashboard/src/app/api/session/route.test.ts`
- `apps/telegram-business-dashboard/src/app/api/business/route-handlers.test.ts`
- Task package reports/progress/verification files under `docs/plans/2026-05-26-telegram-business-media/`.

## Spec compliance
- Fresh initData validates as before with 5-minute max age: done; existing rejection tests still pass.
- `POST /api/session` issues 24-hour session cookie: done; cookie is HMAC-signed, HttpOnly, Secure, `SameSite=None`, `Path=/`, `Max-Age=86400` with expiry.
- Business routes accept fresh initData or valid cookie: done; auth gate prefers fresh initData and falls back to cookie.
- Fresh initData may refresh cookie: done; Business route responses attach refreshed cookie when initData authenticated the request.
- Expired/tampered cookie rejection: done.
- Service token server-only: done; existing exposure regression passes and no client token exposure added.

## Acceptance verification
- Command: `cd apps/telegram-business-dashboard && npm run test:auth -- src/app/api/session/route.test.ts src/app/api/business/route-handlers.test.ts src/lib/server/telegram-auth.test.ts && npm run typecheck && npm run lint`
- Result: passed.
- Evidence: Vitest reported `3 passed` files and `27 passed` tests; `tsc --noEmit` passed; `eslint` passed.

## Issues
### Issue R-01: Short-lived initData-only auth replaced by server lease fallback
- Resolution: Added stateless signed dashboard session cookie helpers and Business BFF fallback auth.
- Evidence: changed auth helpers/routes and passing targeted tests.

Blocking issues: none.
Follow-up issues: none identified for this slice.

## System readiness
- Routes / registration: ready; existing Next route files updated.
- Services / APIs: ready; upstream Hermes token forwarding unchanged and server-only.
- Config / secrets: ready; no new env var required; signing uses server-only `TELEGRAM_BOT_TOKEN`.
- Frontend-backend integration: compatible; existing fresh initData clients continue working, cookie fallback now covers later requests.
- Deployment: not performed per instruction.

## Verdict
Done locally. Implementation and targeted verification completed. No deploy or push performed.
