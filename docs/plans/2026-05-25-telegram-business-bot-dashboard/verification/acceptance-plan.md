## Task package
- Task name: Telegram Business Telegram Web App dashboard — Task 1 Next.js + shadcn setup
- Task package: `docs/plans/2026-05-25-telegram-business-bot-dashboard/`
- Report path: `docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/acceptance-auditor.md`
- Acceptance plan path: `docs/plans/2026-05-25-telegram-business-bot-dashboard/verification/acceptance-plan.md`

## Acceptance criteria to audit
- Separate Next.js app exists at `apps/telegram-business-dashboard/`.
- App uses App Router, TypeScript, Tailwind, and shadcn/ui.
- Telegram Web App bootstrap loads Telegram JS, calls `ready()`/`expand()`, and degrades gracefully outside Telegram.
- Server-only Telegram initData validation helper exists.
- Owner/admin-only session route exists.
- `.env.example` includes required env names and no secrets.
- App builds locally without Hermes API implementation.
- Vercel root directory is documented.
- BotFather/menu setup is documented.
- Caddy/Nginx notes for later VPS API exposure are documented.

## Evidence collected
- Fresh local checks in `apps/telegram-business-dashboard/`:
  - `npm run lint` — passed
  - `npm run typecheck` — passed
  - `npm run build` — passed
- File evidence:
  - `apps/telegram-business-dashboard/package.json`
  - `apps/telegram-business-dashboard/src/app/layout.tsx`
  - `apps/telegram-business-dashboard/src/app/page.tsx`
  - `apps/telegram-business-dashboard/src/app/api/session/route.ts`
  - `apps/telegram-business-dashboard/src/lib/server/telegram-auth.ts`
  - `apps/telegram-business-dashboard/src/lib/telegram/use-telegram-webapp.ts`
  - `apps/telegram-business-dashboard/.env.example`
  - `apps/telegram-business-dashboard/README.md`
  - `docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/task-1-next-shadcn-telegram-setup.md`
- Browser evidence:
  - `docs/plans/2026-05-25-telegram-business-bot-dashboard/artifacts/task-1-open-from-telegram.png`
- Auth smoke evidence:
  - admin 200
  - nonadmin 403
  - expired 401
  - invalid 401

## Audit status
- No open evidence gaps remain for Task 1.
- Acceptance is ready for final auditor verdict.