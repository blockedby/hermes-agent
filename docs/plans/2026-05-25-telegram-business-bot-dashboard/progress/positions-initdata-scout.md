# Progress

## Status
In Progress

## Tasks
- Reviewed Telegram Mini App auth/bootstrap flow in `telegram-business-dashboard` vs `positions` frontend.
- Root cause appears to be Telegram SDK/auth bootstrap timing plus a missing client-side session exchange.

## Files Changed
- None (inspection only).

## Notes
- `apps/telegram-business-dashboard/src/lib/telegram/use-telegram-webapp.ts:31-77` waits for `window.Telegram.WebApp.initData` before calling `ready()/expand()` and times out after 1s.
- `apps/telegram-business-dashboard/src/app/layout.tsx:40-45` loads Telegram SDK via `next/script`, but there is no synchronous bootstrap like `positions/frontend/src/main.tsx:12-21`.
- `apps/telegram-business-dashboard/src/app/api/session/route.ts:13-38` validates initData, but no client code posts to it.
- `apps/telegram-business-dashboard/src/lib/business/api.ts:37-56` sends `x-telegram-init-data` on every request, so if the hook misses initData once, the dashboard stays unauthorized.
