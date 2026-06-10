PI_RESULT: PASS
TASK: Task 8 preliminary dashboard settings contract
TASK_PACKAGE: docs/plans/2026-06-09-telegram-business-dialog-profiles
REPORT_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task8-dashboard-settings-contract.md
PROGRESS_PATH: docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task8-dashboard-settings-contract.md
COMMITS:
- c60cc687c: feat(dashboard): add business settings route contract
FILES_CHANGED:
- apps/telegram-business-dashboard/src/lib/business/types.ts: added settings response/patch/invocation-policy contract types.
- apps/telegram-business-dashboard/src/lib/business/api.ts: added GET/PATCH settings client methods and safe PATCH support in `businessFetch`.
- apps/telegram-business-dashboard/src/app/api/business/chats/[token]/settings/route.ts: added BFF GET/PATCH route using existing auth/session/safe Hermes response helpers.
- apps/telegram-business-dashboard/src/lib/server/hermes-dashboard-api.ts: allowed PATCH in dashboard upstream helper and re-exported settings response type.
- apps/telegram-business-dashboard/src/lib/server/business-route.ts: allowed `invalid_settings` and `invalid_invocation_policy` through safe public error mapping.
- apps/telegram-business-dashboard/src/lib/business/business-api.test.ts: covered settings client GET/PATCH request shape and no service-token exposure.
- apps/telegram-business-dashboard/src/app/api/business/route-handlers.test.ts: covered settings route forwarding, auth rejection, allowed-key filtering, actor forwarding, and validation error mapping.
- docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task8-dashboard-settings-contract.md: implementation progress/evidence notes.
AC_VERIFICATION:
- API client sends GET and PATCH to `/api/business/chats/:token/settings` with Telegram initData only in BFF-facing headers/body as appropriate and no service token exposure: targeted container Vitest passed for `business-api.test.ts` settings client case — passed.
- BFF GET forwards to Hermes with bearer service token and `x-telegram-user-id` actor header: targeted container Vitest passed for settings GET route with initData and dashboard session cookie auth — passed.
- BFF PATCH forwards only allowed settings keys plus actorUserId; does not forward initData or unknown keys: targeted container Vitest passed for settings PATCH route body assertions — passed.
- Existing route auth/session-cookie behavior is preserved; missing auth rejects before upstream call: targeted container Vitest passed for missing-auth settings GET/PATCH plus existing route auth tests — passed.
- Error mapping remains via existing safe response layer; add `invalid_settings`/`invalid_invocation_policy` to public client errors if needed: targeted container Vitest passed for nested `invalid_invocation_policy` mapping; code also whitelists `invalid_settings` — passed.
TESTS_RUN:
- `docker compose -f docker-compose.test.yml run --rm --build build-assets bash -lc 'cd apps/telegram-business-dashboard && npm run test:auth -- src/lib/business/business-api.test.ts src/app/api/business/route-handlers.test.ts'`: RED failed as expected before implementation (`fetchBusinessChatSettings is not a function`; missing settings route).
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run test:auth -- src/lib/business/business-api.test.ts src/app/api/business/route-handlers.test.ts`: GREEN passed, 2 files / 23 tests.
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run test:auth`: failed in pre-existing UI component tests (`Invalid hook call` / `Cannot read properties of null (reading 'useRef')` in `business-dashboard-ui.test.tsx`); targeted files passed in same run.
- `docker run --rm -w /workspace/apps/telegram-business-dashboard hermes-agent:test-runner-assets npm run test:auth -- src/components/business/business-dashboard-ui.test.tsx`: failed with the same invalid-hook-call error against cached image without current source bind mount, indicating baseline/container issue outside this prelim contract slice.
QUALITY_CHECKS:
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run lint`: passed.
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run typecheck`: passed.
- `git diff --check`: passed.
- `docker run --rm -w /workspace/apps/telegram-business-dashboard hermes-agent:test-runner-assets npm run build`: failed on cached image baseline with Next/Turbopack workspace-root inference (`couldn't find next/package.json` from `src/app`); not caused by this source change.
QUALITY_NOTES:
- Readability/reuse: Reused existing `businessFetch`, `authenticateTelegramAdmin`, `postBodyWithoutInitData`, `callHermesDashboard`, `safeHermesResponse`, and session-cookie helpers; no new abstraction added.
- Error handling/logging: Preserved existing BFF safe response mapping and added only scoped public validation error codes.
- Backend/API/data: BFF forwards only route-contract payloads; no backend Python/storage implementation touched.
- Frontend/UI: No UI component work in this prelim slice; client API/type contract only.
- DevOps/runtime: No env/config/deployment changes.
- Security: Service token remains server-only; BFF strips `initData` and unknown PATCH keys before upstream forwarding; no sensitive logging added.
- Concurrency/idempotency: No persisted writes implemented in this slice; PATCH forwarding remains a single upstream call.
- Compatibility/performance: Existing route/client contracts preserved; added method support is additive and no hot-loop/per-request extra network calls introduced.
SIDE_FINDINGS:
- Blocking: none for delegated prelim contract implementation.
- Non-blocking follow-up candidates: baseline container full dashboard test/build issues remain (`business-dashboard-ui.test.tsx` invalid hook call; Next/Turbopack workspace-root build inference).
PARENT_ACTION_REQUIRED:
- Action: none.
- Reason: n/a.
- Expected evidence: n/a.
- Safety bounds: n/a.
NOTES: Implementation is scoped to the preliminary settings types/client/BFF contract. It intentionally does not implement backend Python settings persistence or dashboard UI components.
