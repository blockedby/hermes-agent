# Local verification — Hermes fork attribution

## Git evidence
32d3f0449 fix: sync upstream and harden codex responses
c0fcb0792 docs: record dashboard session lease plan
0f180e6b5 docs: report Telegram dashboard session lease implementation
3011c9568 feat: add Telegram dashboard session lease
ea07cd470 fix: keep business draft generation in dashboard
8da24bb2e fix: embed telegram business dashboard API
7b5db852a feat: ingest telegram business media
52d93fa27 fix: capture telegram launch init data
26f7b4580 docs: record dashboard final acceptance audit
f1e414864 docs: record telegram business dashboard final verification
9f6574da3 docs: add dashboard browser smoke evidence
ef20a8bb6 docs: report telegram dashboard reviewer fixes
954d4f60a fix: harden telegram business dashboard API
6f98d1610 docs: add task 7 implementation report
3a341c5e8 feat: add telegram business dashboard launcher
cbd8fc42c docs: report telegram business dashboard UI task
d0808d9d2 feat: add telegram business dashboard UI
3fc21c933 docs: report telegram business dashboard BFF task
5418f2cb2 feat: add telegram business dashboard BFF routes
ccde7f3da docs: report telegram business history task
f3be21ea1 feat: record telegram business dashboard history
0c1cada66 docs: report telegram business dashboard api task
3228303c2 feat: add telegram business dashboard API
5a293fd4a docs: record task 2 auth evidence
4e7582668 test: cover Telegram dashboard auth
6ffa1b983 feat: scaffold telegram business dashboard
49baf28c6 fix: keep telegram business thread marker out of dm topic
66c9ea6fc fix: initialize telegram business runtime state
07eeeb538 fix: resolve upstream rebase regressions
4bfb9c75e fix: frame telegram business replies as owner drafts
58f2ccebf test: align read_image integration regressions
763a9f2d6 feat: document non-vision read_image fallback
f4a46e474 feat: expose read_image as primary vision path
f6d31aeee feat(read-image): add safe HTTP image loading
2e2c89e90 test: cover multimodal tool result regressions
93b8051f0 feat: add native read_image local MVP
51a71d122 fix: trigger business mode actions immediately
0446b4e5c fix: preserve business session key fallback routing
28606f1d0 feat: add Telegram Business per-chat modes
47ac13c54 test: add hermetic Docker test runner

## Diff stat selected
 apps/telegram-business-dashboard/.env.example      |    15 +
 apps/telegram-business-dashboard/.gitignore        |    42 +
 apps/telegram-business-dashboard/AGENTS.md         |     5 +
 apps/telegram-business-dashboard/CLAUDE.md         |     1 +
 apps/telegram-business-dashboard/README.md         |    66 +
 apps/telegram-business-dashboard/components.json   |    25 +
 apps/telegram-business-dashboard/eslint.config.mjs |    18 +
 apps/telegram-business-dashboard/next.config.ts    |    40 +
 apps/telegram-business-dashboard/package-lock.json | 10901 +++++++++++++++++++
 apps/telegram-business-dashboard/package.json      |    42 +
 .../telegram-business-dashboard/postcss.config.mjs |     7 +
 apps/telegram-business-dashboard/public/file.svg   |     1 +
 apps/telegram-business-dashboard/public/globe.svg  |     1 +
 apps/telegram-business-dashboard/public/next.svg   |     1 +
 apps/telegram-business-dashboard/public/vercel.svg |     1 +
 apps/telegram-business-dashboard/public/window.svg |     1 +
 .../app/api/business/chats/[token]/draft/route.ts  |    48 +
 .../api/business/chats/[token]/history/route.ts    |    48 +
 .../app/api/business/chats/[token]/mode/route.ts   |    48 +
 .../src/app/api/business/chats/[token]/route.ts    |    36 +
 .../src/app/api/business/chats/route.ts            |    40 +
 .../src/app/api/business/route-handlers.test.ts    |   450 +
 .../src/app/api/session/route.test.ts              |   137 +
 .../src/app/api/session/route.ts                   |    48 +
 .../src/app/chats/[token]/page.tsx                 |    10 +
 .../src/app/favicon.ico                            |   Bin 0 -> 25931 bytes
 .../src/app/globals.css                            |   130 +
 .../telegram-business-dashboard/src/app/layout.tsx |    49 +
 apps/telegram-business-dashboard/src/app/page.tsx  |     5 +
 .../business/business-dashboard-ui.test.tsx        |   195 +
 .../src/components/business/chat-detail-shell.tsx  |   201 +
 .../src/components/business/chat-detail-view.tsx   |   272 +
 .../src/components/business/dashboard-shell.tsx    |    72 +
 .../src/components/business/dashboard-view.tsx     |   255 +
 .../src/components/ui/alert.tsx                    |    76 +
 .../src/components/ui/badge.tsx                    |    52 +
 .../src/components/ui/button.tsx                   |    58 +
 .../src/components/ui/card.tsx                     |   103 +
 .../src/components/ui/separator.tsx                |    25 +
 .../src/components/ui/skeleton.tsx                 |    13 +
 .../src/components/ui/tabs.tsx                     |    82 +
 .../src/lib/business/api.ts                        |    96 +
 .../src/lib/business/business-api.test.ts          |   114 +
 .../src/lib/business/types.ts                      |    68 +
 .../src/lib/business/view-model.ts                 |    93 +
 .../src/lib/server/business-route.ts               |   166 +
 .../src/lib/server/hermes-dashboard-api.ts         |    99 +
 .../src/lib/server/telegram-auth.test.ts           |    70 +
 .../src/lib/server/telegram-auth.ts                |   196 +
 .../src/lib/telegram/launch-params.test.ts         |    76 +
 .../src/lib/telegram/launch-params.ts              |    73 +
 .../src/lib/telegram/use-telegram-webapp.ts        |   115 +
 apps/telegram-business-dashboard/src/lib/utils.ts  |     6 +
 .../src/test/server-only-stub.ts                   |     1 +
 .../src/test/telegram-init-data-fixtures.ts        |    26 +
 .../src/types/telegram-web-app.d.ts                |    59 +
 apps/telegram-business-dashboard/tsconfig.json     |    34 +
 apps/telegram-business-dashboard/vitest.config.mts |    22 +
 docs/telegram-business-modes.md                    |   199 +
 gateway/platforms/telegram.py                      |  2604 ++++-
 gateway/run.py                                     |   242 +-
 gateway/session.py                                 |    21 +-
 hermes_cli/config.py                               |     8 +
 tests/gateway/test_config.py                       |    43 +
 tests/gateway/test_send_image_file.py              |    48 +-
 tests/gateway/test_session.py                      |    23 +
 tests/gateway/test_session_key_parse_fallback.py   |    55 +
 tests/gateway/test_stt_config.py                   |    58 +
 tests/gateway/test_telegram_approval_buttons.py    |     2 +-
 tests/gateway/test_telegram_business.py            |  2160 ++++
 .../test_telegram_business_dashboard_api.py        |   410 +
 tests/gateway/test_telegram_documents.py           |     4 +-
 tests/gateway/test_telegram_session_isolation.py   |    40 +
 tests/gateway/test_telegram_thread_fallback.py     |    49 +-
 tests/hermes_cli/test_api_key_providers.py         |     1 +
 tests/hermes_cli/test_auth_ssl_macos.py            |     2 +-
 website/docs/user-guide/messaging/telegram.md      |    29 +
 77 files changed, 20749 insertions(+), 183 deletions(-)

## First 10 lines
     1	# My changes in blockedby's Hermes Agent fork
     2
     3	Hermes Agent is an upstream open-source project by NousResearch and the Hermes Agent maintainers.
     4	This file does not claim original authorship of Hermes Agent.
     5	It summarizes selected engineering work in Alexander Longov's (`blockedby`) public fork:
     6	<https://github.com/blockedby/hermes-agent>.
     7
     8	The focus of this fork work is Telegram Business gateway behavior, messaging/session reliability,
     9	and public verification evidence for the fork.
    10

## git diff --check
PASS: no whitespace errors

## Forbidden phrase / overclaim scan
PASS: no forbidden phrase or upstream ownership overclaim found

## Secret/private URL scan
PASS: no token-like strings, private webhook/chat URLs, or key assignments found

## Status
## alex/github-portfolio-hermes-attribution
?? MY_CHANGES.md
?? docs/plans/2026-06-02-hermes-fork-attribution/
