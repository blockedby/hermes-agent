PI_RESULT: PASS
TASK: Task 7 — Bot launcher + VPS/Vercel deployment wiring
TASK_PACKAGE: docs/plans/2026-05-25-telegram-business-bot-dashboard
REPORT_PATH: docs/plans/2026-05-25-telegram-business-bot-dashboard/reports/task-7-launcher-deploy.md
PROGRESS_PATH: docs/plans/2026-05-25-telegram-business-bot-dashboard/progress/aad-implementer-task-7-launcher-deploy.md
COMMITS:
- 3a341c5e8facd681825916c244cb6ce545f7513a: feat: add telegram business dashboard launcher
FILES_CHANGED:
- gateway/platforms/telegram.py: Added `telegram.business_dashboard_webapp_url`/`TELEGRAM_BUSINESS_DASHBOARD_WEBAPP_URL` resolver and `/business` Telegram Web App launcher button with inline-panel fallback when unset.
- gateway/config.py: Bridged top-level `telegram.business_dashboard_webapp_url` into Telegram platform runtime extra config, with env override support.
- hermes_cli/config.py: Added default config key and optional env metadata for `TELEGRAM_BUSINESS_DASHBOARD_WEBAPP_URL`.
- tests/gateway/test_telegram_business.py: Added configured Web App launcher, missing fallback, resolver precedence, and no configured-URL logging coverage.
- tests/gateway/test_config.py: Added gateway config/env bridge tests.
- docs/telegram-business-modes.md: Documented launcher config, rollback, standalone API entrypoint, systemd user unit, Caddy/Nginx proxy examples, and Vercel env names.
- apps/telegram-business-dashboard/README.md: Documented wiring the deployed Vercel URL back into Hermes gateway config/env.
- apps/telegram-business-dashboard/.env.example: Added comment linking `NEXT_PUBLIC_TELEGRAM_WEBAPP_URL` to Hermes launcher config/env.
- docs/plans/2026-05-25-telegram-business-bot-dashboard/progress/aad-implementer-task-7-launcher-deploy.md: Progress and verification notes.
AC_VERIFICATION:
- `/business` shows `Open dashboard` Web App button when configured: `test_business_command_sends_webapp_launcher_when_dashboard_url_configured` passed; asserted button text and `web_app.url` — passed.
- Missing dashboard URL falls back to old inline panel: `test_business_command_falls_back_to_inline_panel_without_dashboard_url` passed; asserted `Known chats` panel and no Web App buttons — passed.
- Config/env support for launcher URL: `test_bridges_telegram_business_dashboard_webapp_url_from_config_yaml`, `test_telegram_business_dashboard_webapp_url_env_takes_precedence`, and `test_business_dashboard_webapp_url_prefers_config_over_env` passed — passed.
- No-secret/no-URL logging for launcher: configured URL containing `preview_secret=do-not-log` was absent from captured Telegram adapter log messages in the launcher test — passed.
- Vercel app required env documented: `apps/telegram-business-dashboard/README.md`, `.env.example`, and `docs/telegram-business-modes.md` list Vercel env names and server-only token guidance — passed by docs inspection and app lint/build.
- VPS API standalone/runtime docs: `docs/telegram-business-modes.md` documents `python -m gateway.platforms.telegram_business_dashboard_api`, user systemd service, Caddy/Nginx reverse proxy, bind/port/token env names — passed by docs inspection; live VPS start/restart not run per “Do not deploy” instruction.
- Telegram Web App can load from bot and fetch real chat data: launcher wiring and app build passed locally; real Telegram/Vercel/VPS smoke not run per “Do not deploy or push” instruction — not run.
TESTS_RUN:
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_config.py -- -q --tb=short -k 'business_dashboard_webapp_url or business_command_sends_webapp_launcher or business_command_falls_back'`: RED failed as expected before implementation (4 failing tests), then GREEN passed (5 tests).
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_config.py -- -q --tb=short`: passed, 118 tests.
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_config.py -- -q --tb=short`: passed, 129 tests.
QUALITY_CHECKS:
- `venv/bin/python -m compileall -q gateway/platforms/telegram.py gateway/config.py hermes_cli/config.py tests/gateway/test_telegram_business.py tests/gateway/test_config.py`: passed.
- `cd apps/telegram-business-dashboard && npm run lint`: passed.
- `cd apps/telegram-business-dashboard && npm run build`: passed.
- `git diff --check`: passed.
QUALITY_NOTES:
- Readability/reuse: Reused existing `/business` owner authorization path, Telegram owner chat/thread helpers, `InlineKeyboardMarkup`/`InlineKeyboardButton` patterns, and gateway config bridge style.
- Error handling/logging: Added no new logging for configured URLs or token-bearing values; existing unauthorized `/business` handling unchanged.
- Backend/API/data: No persistence schema or API response contract changes; dashboard API regression tests still pass.
- Frontend/UI: No UI code changes; app docs/env linkage updated, and lint/build stayed green.
- DevOps/runtime: Paired gateway config/env support with default config metadata, app env docs, Vercel root/env guidance, standalone API systemd unit, and Caddy/Nginx examples.
- Security: No secrets committed; service token remains server-only in docs; launcher URL is treated as config and not logged; no auth/authorization weakening.
- Concurrency/idempotency: Not relevant for launcher; `/business` remains a single owner-command send path.
- Compatibility/performance: Missing URL preserves old inline panel; configured path adds one lightweight branch and avoids loading chat store data for launcher sends.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: Real Telegram/Vercel/VPS smoke remains for Task 8/final verification because this task was instructed not to deploy or push.
NOTES: Successful pytest evidence used `HERMES_TEST_VENV=$PWD/venv` because the default `.venv` lacks pytest in this checkout.
