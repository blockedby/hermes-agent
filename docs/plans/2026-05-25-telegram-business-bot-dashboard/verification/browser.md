# Browser verification

## 2026-05-25 headless smoke: outside Telegram unauthorized state

- Report: `docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/browser-smoke.md`
- App directory: `apps/telegram-business-dashboard`
- Server command: `npm run start -- -p 3107 -H 127.0.0.1`
- Browser: disposable headless Chromium via Playwright with `/usr/bin/chromium`
- Route: `http://127.0.0.1:3107/`
- Result: PASS

Evidence:
- Mobile screenshot: `docs/plans/2026-05-25-telegram-business-bot-dashboard/artifacts/screenshots/browser-smoke/2026-05-25T191123Z/390x844-mobile-unauthorized.png`
- Desktop screenshot: `docs/plans/2026-05-25-telegram-business-bot-dashboard/artifacts/screenshots/browser-smoke/2026-05-25T191123Z/1280x800-desktop-unauthorized.png`
- Raw browser metrics: `docs/plans/2026-05-25-telegram-business-bot-dashboard/artifacts/screenshots/browser-smoke/2026-05-25T191123Z/smoke-results.json`
- Server log: `docs/plans/2026-05-25-telegram-business-bot-dashboard/verification/logs/telegram-dashboard-server-2026-05-25T191123Z.log`

Findings:
- Outside Telegram, the app settles into the expected unauthorized state: `Open from Telegram` / `Launch this dashboard from the Telegram bot with an allowed owner account.`
- Mobile 390x844 had no horizontal overflow (`scrollWidth=390`, `clientWidth=390`) and no viewport-bound offenders.
- Desktop 1280x800 also had no horizontal overflow.
- No console errors/warnings, failed requests, or HTTP error responses were observed during the smoke.
