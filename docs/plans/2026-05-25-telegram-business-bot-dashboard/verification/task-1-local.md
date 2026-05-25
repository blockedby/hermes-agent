# Task 1 local verification

Date: 2026-05-25
Scope: `apps/telegram-business-dashboard`

## Static/build checks

```bash
cd /home/kcnc/code/hermes/hermes-agent/apps/telegram-business-dashboard
npm run lint
npm run typecheck
npm run build
```

Result:

```text
lint: pass
typecheck: pass
build: pass
Next.js workspace-root warning: resolved; no warning in latest build.
```

## Dev HTTP smoke

Command shape:

```bash
npm run dev
curl http://localhost:3000/
curl -X POST http://localhost:3000/api/session -H 'content-type: application/json' -d '{}'
```

Evidence:

```text
GET / -> 200
POST /api/session {} -> 400 {"ok":false,"error":"missing_init_data"}
```

## Auth path smoke

With env:

```bash
TELEGRAM_BOT_TOKEN='123456:test-token'
TELEGRAM_ADMIN_USER_IDS='123456789'
```

Signed initData generated with `@tma.js/init-data-node`.

Results:

```text
admin:    200 {"ok":true,"user":{"telegramUserId":123456789,"username":"user123456789","firstName":"Test"}}
nonadmin: 403 {"ok":false,"error":"forbidden"}
expired:  401 {"ok":false,"error":"unauthorized"}
invalid:  401 {"ok":false,"error":"unauthorized"}
```

## Browser smoke

Headless Chrome loaded:

```text
http://localhost:3000/
```

Expected outside Telegram:

```text
Open from Telegram
This dashboard is available only when launched as a Telegram Web App.
```

Screenshot artifact:

```text
docs/plans/2026-05-25-telegram-business-bot-dashboard/artifacts/task-1-open-from-telegram.png
```

## Notes

- `127.0.0.1` dev smoke triggered Next dev allowed-origin warnings for dev resources. Browser smoke used `localhost`, which matches Next dev origin and avoids the warning.
- No real secrets were used.
