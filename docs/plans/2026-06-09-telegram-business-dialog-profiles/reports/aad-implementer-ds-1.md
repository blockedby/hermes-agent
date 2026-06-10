PI_RESULT: PASS
TASK: dashboard-settings-invalid-settings-fix / DS-1
TASK_PACKAGE: docs/plans/2026-06-09-telegram-business-dialog-profiles
REPORT_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-ds-1.md
PROGRESS_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-ds-1.md
COMMITS:
- ba1273715065150c81afc99088b75c964fe43318: fix(dashboard): stop forwarding actor in settings body
FILES_CHANGED:
- apps/telegram-business-dashboard/src/lib/server/hermes-dashboard-api.ts: removed global `actorUserId` merge into JSON request bodies while retaining `X-Telegram-User-Id` header construction.
- apps/telegram-business-dashboard/src/app/api/business/route-handlers.test.ts: updated mode/settings/draft route-handler expectations to assert sanitized forwarded bodies; settings PATCH now asserts exact allowed settings keys and excludes `actorUserId`, `initData`, and unknown keys.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-ds-1.md: recorded DS-1 progress and TDD evidence.
AC_VERIFICATION:
- Settings PATCH forwarded request has `X-Telegram-User-Id` header: route-handler test `PATCHes chat settings with actor header and exactly allowed settings keys` asserts the header in the forwarded fetch call — passed in container.
- Settings PATCH forwarded JSON body contains exactly allowed settings keys supplied by route sanitization: same test compares the parsed forwarded body exactly to `assistantDisplayName`, `assistantPrefix`, `dialogPrompt`, `dialogNotes`, and `invocationPolicy` — passed in container.
- Settings PATCH forwarded JSON body excludes `actorUserId`, `initData`, and unknown client keys: same test asserts all three are absent after posting a body containing `initData` and `unknownKey`; helper no longer injects `actorUserId` — passed in container.
- Route-handler tests are updated so no test expects implicit body actor unless a route deliberately includes it: mode and draft tests now expect sanitized bodies without implicit `actorUserId`; grep of route-handler test shows only negative `not.toHaveProperty("actorUserId")` assertions remain — passed.
TESTS_RUN:
- RED: `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run test:auth -- src/app/api/business/route-handlers.test.ts` — failed as expected before production change, 3 failures showing injected `actorUserId` in mode/settings/draft JSON bodies.
- GREEN/targeted: `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run test:auth -- src/app/api/business/route-handlers.test.ts` — passed, 1 file / 19 tests.
QUALITY_CHECKS:
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run typecheck` — passed.
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run lint` — passed.
- `grep actorUserId apps/telegram-business-dashboard/src/app/api/business/route-handlers.test.ts` via repo search — only negative absence assertions remain in route-handler body expectations.
QUALITY_NOTES:
- Readability/reuse: reused existing `callHermesDashboard` header construction and route-level `postBodyWithoutInitData` sanitization; no new abstraction was needed.
- Error handling/logging: unchanged; safe Hermes response mapping and auth flow are preserved.
- Backend/API/data: BFF forwarding contract now preserves sanitized route body exactly and conveys actor identity only via the existing `X-Telegram-User-Id` header, matching the strict gateway settings API validation.
- Frontend/UI: not applicable; no UI components changed.
- DevOps/runtime: no env, deployment, Docker, or runtime wiring changes.
- Security: no sensitive logging added; service token remains server-only; auth header/session validation behavior unchanged.
- Concurrency/idempotency: not relevant for this stateless request-forwarding change.
- Compatibility/performance: public route paths/status handling unchanged; endpoint body contract intentionally removes previously implicit actor body injection per DS-1 scope.
SIDE_FINDINGS:
- Blocking: none.
- Non-blocking follow-up candidates: live Vercel/prod verification remains outside this implementer scope.
PARENT_ACTION_REQUIRED:
- Action: none.
- Reason: none.
- Expected evidence: none.
- Safety bounds: none.
NOTES: Container-only verification was used as requested; no host npm/pytest/uv commands were run. Pre-existing modified `docs/plans/2026-06-09-telegram-business-dialog-profiles/plan.md` was left untouched/uncommitted.
