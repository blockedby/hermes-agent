## Task package
- Task name: Telegram Business Dashboard browser smoke
- Task package: `docs/plans/2026-05-25-telegram-business-bot-dashboard`
- Report path: `docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/browser-smoke.md`
- Screenshot artifact root: `docs/plans/2026-05-25-telegram-business-bot-dashboard/artifacts/screenshots/browser-smoke/2026-05-25T191123Z/`
- Scope: app loaded outside Telegram / unauthorized state
- URL / route: `http://127.0.0.1:3107/`

## Method
- Started production server from `apps/telegram-business-dashboard` with `npm run start -- -p 3107 -H 127.0.0.1`.
- Used disposable headless Chromium via Playwright and system `/usr/bin/chromium`.
- Loaded the app without Telegram WebApp init data, waited for the missing-Telegram retry loop to settle, then captured screenshots and DOM/browser metrics.
- Server log: `docs/plans/2026-05-25-telegram-business-bot-dashboard/verification/logs/telegram-dashboard-server-2026-05-25T191123Z.log`.

## Screenshot matrix
| Viewport | Section / scroll | Artifact path | Hard failures | Soft score |
| --- | --- | --- | --- | --- |
| 390x844 | unauthorized/top | `docs/plans/2026-05-25-telegram-business-bot-dashboard/artifacts/screenshots/browser-smoke/2026-05-25T191123Z/390x844-mobile-unauthorized.png` | none | 1; composition 0, readability 0, spacing/alignment 0, responsive awkwardness 1, product-quality 0 |
| 1280x800 | unauthorized/top | `docs/plans/2026-05-25-telegram-business-bot-dashboard/artifacts/screenshots/browser-smoke/2026-05-25T191123Z/1280x800-desktop-unauthorized.png` | none | 1; composition 0, readability 0, spacing/alignment 0, responsive awkwardness 0, product-quality 1 |

## Worst screenshot
- Path: `docs/plans/2026-05-25-telegram-business-bot-dashboard/artifacts/screenshots/browser-smoke/2026-05-25T191123Z/390x844-mobile-unauthorized.png`
- Viewport: 390x844
- Section / scroll: unauthorized/top
- Hard failures: none
- Soft risk score: 1; composition 0, readability 0, spacing/alignment 0, responsive awkwardness 1, product-quality 0
- Why this is worst: mobile shows the expected unauthorized state and no clipping, but the count-card grid leaves the final card alone on the last row; this is mild responsive awkwardness, not a blocking failure.

## First-glance verdict
- Verdict: pass
- Would a product owner reject this screenshot immediately? no
- Reason: The app renders a safe unauthenticated state outside Telegram with a clear `Open from Telegram` message, readable text, and no obvious layout breakage.

## Issues by priority
1. None blocking. The unauthorized state is visible and clear on mobile and desktop.
2. Minor polish: mobile count cards form a 2-column grid with an orphan `Failed drafts` card on its own row; acceptable for smoke, but could be refined later.

## Objective supporting checks
- Horizontal overflow: passed. Mobile `scrollWidth=390`, `clientWidth=390`; desktop `scrollWidth=1280`, `clientWidth=1280`.
- Clipped or overlapped elements: passed by screenshot review; no visible clipped labels, buttons, search input, or unauthorized alert.
- DOM intersections: passed for overflow scan; no elements extended beyond viewport bounds in either tested viewport.
- Console/network blockers: passed. No console errors/warnings, no failed requests, no HTTP 4xx/5xx responses during the smoke. Browser logged only Telegram WebView compatibility `postEvent` messages.
- Missing/broken assets: passed by screenshot review and network failure scan.

## Coverage gaps and waivers
- Missing viewports/sections: only 390x844 mobile and 1280x800 desktop were captured for this smoke. Full tablet/wide visual review was not requested.
- Waivers: none.
- Stale evidence risk: local production server was started from the current worktree; screenshots represent that local state at `2026-05-25T191123Z`.

## Recommendation
- Status: pass
- Next action: accept this browser smoke evidence for outside-Telegram/unauthorized rendering; route only optional mobile grid polish if desired.
