## Task
- Mission: Fix Telegram Business dashboard settings save failure (`invalid_settings`) caused by forwarding `actorUserId` in the settings PATCH JSON body.
- Target: `apps/telegram-business-dashboard` BFF forwarding helper and route-handler tests.
- Boundaries: Narrow BFF/test fix only; no gateway validation relaxation, UI redesign, or host npm/pytest/uv.
- Done when: settings PATCH forwards actor in `X-Telegram-User-Id` header while the JSON body contains only allowed settings keys.

## Context
- Slice stayed whole; implementation was delegated to one `aad-implementer` task (DS-1), no sub-slices.
- Worktree: `/home/kcnc/code/hermes/hermes-agent/.worktrees/telegram-business-dialog-profiles`
- Branch: `feat/telegram-business-dialog-profiles`
- Task package: `docs/plans/2026-06-09-telegram-business-dialog-profiles`
- Implementer report: `docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-ds-1.md`

## Changes
- `apps/telegram-business-dashboard/src/lib/server/hermes-dashboard-api.ts`: `callHermesDashboard` no longer merges `actorUserId` into JSON request bodies; it still sends `x-telegram-user-id`.
- `apps/telegram-business-dashboard/src/app/api/business/route-handlers.test.ts`: updated mode/draft/settings body expectations; settings PATCH now proves exact allowed settings keys and absence of `actorUserId`, `initData`, and `unknownKey`.

## Commits
- `ba1273715065150c81afc99088b75c964fe43318` `fix(dashboard): stop forwarding actor in settings body`
- `a3e5ac2aa` `docs: report dashboard settings body fix`

## Acceptance verification
- AC1 actor remains conveyed via header: passed.
  - Evidence: settings PATCH route-handler assertion includes `"x-telegram-user-id": String(TEST_ADMIN_USER_ID)`.
- AC2 settings PATCH body contains only allowed settings keys: passed.
  - Evidence: updated test compares parsed upstream body exactly to `assistantDisplayName`, `assistantPrefix`, `dialogPrompt`, `dialogNotes`, `invocationPolicy`.
- AC3 no `actorUserId` / `initData` / unknown key in settings body: passed.
  - Evidence: updated test asserts all three are absent.

## Verification run
Container-only verification; no host npm/pytest/uv commands run.
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run test:auth -- src/app/api/business/route-handlers.test.ts`
  - Passed: 1 file / 19 tests.
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run typecheck`
  - Passed.
- `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run lint`
  - Passed.

## Issues
### Issue R-01: Settings PATCH rejected by strict gateway validation
- Description: Dashboard BFF added `actorUserId` to all JSON bodies, but Telegram Business settings PATCH strictly rejects unknown fields and expects actor identity in the header.
- Evidence: code path in `hermes-dashboard-api.ts`; updated route-handler test fails before helper fix and passes after.
- Resolution: forward sanitized JSON body as-is and keep actor header.

## System readiness
- Services / APIs: ready locally for BFF contract; gateway strict settings validation can remain unchanged.
- Frontend-backend integration: route-handler contract verified.
- Runtime/deployment: local branch ready for PR/deploy pipeline; live Vercel verification not performed in this container-only scope.

## Verdict
- Status: success.
- Goal state: achieved locally.
- Final readiness: ready for review/deployment pipeline with targeted container verification complete.
