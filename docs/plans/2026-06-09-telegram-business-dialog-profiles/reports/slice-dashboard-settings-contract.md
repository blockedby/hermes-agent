## Task
- Mission: Implement the Task 8 preliminary frontend/dashboard settings contract for Telegram Business dialog profiles.
- Target: `apps/telegram-business-dashboard` types, API client, BFF route forwarding, and tests for `GET`/`PATCH /api/business/chats/:token/settings`.
- Boundaries: No backend Python settings persistence; no full dashboard settings UI component; no host npm/pytest/uv. Backend dependency limited to the clear route-forwarding contract in `plan.md` Tasks 2/8.
- Done when: Dashboard contract types/client/BFF route exist, targeted tests pass in container, coherent changes are committed, and progress/report artifacts are updated.
- Expected evidence: Changed files, commits, container-only targeted verification, and known limitations.

## Context
- Thread: PR #25, task package `docs/plans/2026-06-09-telegram-business-dialog-profiles`.
- Slice: dashboard settings contract preliminary Task 8.
- Task package: `docs/plans/2026-06-09-telegram-business-dialog-profiles`.
- Report path: `/tmp/pi-worktree-75ea7da4-2/reports/slice-dashboard-settings-contract.md`.
- Worktree: `/tmp/pi-worktree-75ea7da4-2`.
- Branch: `pi-parallel-75ea7da4-2`.
- Verify scope: dashboard client and BFF route tests only.

## Spec compliance
- Requirement / AC: Implement only if backend settings API contract is clear.
  - Status: done.
  - Evidence: `plan.md` Task 2/8 defines GET/PATCH `/api/business/chats/{token}/settings`, auth, actor, validation, and response contract clearly enough for route-forwarding work.
  - Gap if any: Backend implementation remains outside this slice.
- Requirement / AC: Add dashboard types/API client/BFF route tests for GET/PATCH settings.
  - Status: done.
  - Evidence: commit `c60cc687c feat(dashboard): add business settings route contract`.
  - Gap if any: None for prelim contract scope.

## Acceptance verification
- AC1: API client sends GET/PATCH settings requests without exposing service tokens.
  - Covered by: container Vitest `src/lib/business/business-api.test.ts`.
  - Result: passed.
  - Evidence: targeted container run passed, 4 client tests in file.
- AC2: BFF GET/PATCH forwards to Hermes with actor headers and strips `initData`/unknown fields.
  - Covered by: container Vitest `src/app/api/business/route-handlers.test.ts`.
  - Result: passed.
  - Evidence: targeted container run passed, 19 route tests in file.
- AC3: Existing auth/session behavior preserved and safe error mapping covers settings validation.
  - Covered by: same targeted route tests.
  - Result: passed.
  - Evidence: missing-auth and `invalid_invocation_policy` mapping tests passed.

## System readiness
- Routes / registration: done — added `apps/telegram-business-dashboard/src/app/api/business/chats/[token]/settings/route.ts`.
- Services / APIs: partial by design — frontend/BFF forwarding contract done; backend Python implementation not in this slice.
- Config / env / secrets: done — reused existing server-only dashboard service token path; no new env/secrets.
- Permissions / access: done — reused Telegram admin initData/session-cookie auth and actor forwarding.
- Database / migrations: not relevant to this frontend prelim slice.
- Frontend-backend integration: ready except backend implementation availability.
- Runtime / deployment wiring: no new runtime wiring beyond Next BFF route.

## Verification run
- Local / targeted checks:
  - `docker run --rm -w /workspace/apps/telegram-business-dashboard -v "$PWD/apps/telegram-business-dashboard/src:/workspace/apps/telegram-business-dashboard/src:ro" hermes-agent:test-runner-assets npm run test:auth -- src/lib/business/business-api.test.ts src/app/api/business/route-handlers.test.ts`: passed.
    - Evidence: 2 files passed, 23 tests passed.
- Local / full checks:
  - Implementer reported container `npm run lint`: passed.
  - Implementer reported container `npm run typecheck`: passed.
  - Full dashboard test/build not claimed: broader container runs hit baseline/non-blocking issues (`business-dashboard-ui.test.tsx` invalid hook call; cached image Next/Turbopack workspace-root inference).
- Remote checks / CI:
  - Status: not checked from this slice.

## Issues
### Issue R-01: Dashboard settings contract added
- Description: Task 8 prelim lacked settings types/client/BFF forwarding route.
- Evidence: RED pre-implementation test failed with missing `fetchBusinessChatSettings` and missing settings route; targeted tests now pass.
- Resolution: Added contract types, client functions, route, helper support, safe error mapping, and tests.
- Depends on: Backend settings API implementation for end-to-end runtime.

## Side findings
- Blocking findings folded into active work: none.
- Non-blocking findings tracked separately: not created here; implementer reported existing/baseline container issues in broader dashboard UI tests/build.

## Verdict
- Status: success.
- Goal state: achieved for Task 8 preliminary dashboard settings contract.
- Final readiness: ready except explicit limitation that backend Python settings persistence and full settings UI remain outside this prelim slice.
- Summary: Frontend/dashboard GET/PATCH settings contract is implemented, committed, and container-verified with targeted tests.

## Changed files
- `apps/telegram-business-dashboard/src/lib/business/types.ts`
- `apps/telegram-business-dashboard/src/lib/business/api.ts`
- `apps/telegram-business-dashboard/src/app/api/business/chats/[token]/settings/route.ts`
- `apps/telegram-business-dashboard/src/lib/server/hermes-dashboard-api.ts`
- `apps/telegram-business-dashboard/src/lib/server/business-route.ts`
- `apps/telegram-business-dashboard/src/lib/business/business-api.test.ts`
- `apps/telegram-business-dashboard/src/app/api/business/route-handlers.test.ts`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/reports/aad-implementer-task8-dashboard-settings-contract.md`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/progress/aad-implementer-task8-dashboard-settings-contract.md`
- Owner progress/plan updates pending local commit at report time.

## Commits
- `c60cc687c feat(dashboard): add business settings route contract`
- `98715afaa docs: report dashboard settings contract implementation`
