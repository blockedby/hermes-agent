# Progress

## Status
In Progress

## Tasks

## Files Changed

## Notes

## Review
- Correct: Re-read the Task 1 plan/report and inspected the current Next app/auth files. `next.config.ts` now sets `turbopack.root` to the app directory, and fresh `npm run lint && npm run typecheck && npm run build` passed without the prior workspace-root/multiple-lockfile warning. Dev smoke confirmed `GET /` returns 200 with the expected CSP/security headers and `POST /api/session {}` returns `400 {"ok":false,"error":"missing_init_data"}`.
- Correct: `TELEGRAM_ADMIN_USER_IDS` is used consistently across `.env.example`, README, plan/report docs, and `src/lib/server/telegram-auth.ts`; valid signed admin initData returns 200 and valid non-admin initData returns 403 in a local route smoke.
- Correct: `@tma.js/init-data-node` is server-only in the auth helper and matches the package API for `validate`, `parse`, and `expiresIn`; Telegram BotFather/menu and Caddy/Nginx deployment notes are present in the Task 1 setup report.
- Fixed: No code changes made per instruction.
- Note: The older `verification/acceptance-plan.md` and `reports/acceptance-auditor.md` files still contain stale pre-fix statements about the workspace-root warning and missing docs; I did not edit them because this pass was requested as no-edit except progress.
