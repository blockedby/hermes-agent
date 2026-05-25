## Task
- Mission: Fix Telegram Business dashboard “Generate draft now” so it stays in-place, shows action state, and supports optional prompt/topic pass-through.
- Target: `apps/telegram-business-dashboard` chat detail UI/client/BFF plus `gateway/platforms/telegram_business_dashboard_api.py` draft endpoint.
- Boundaries: No VPS deploy/restart; no broad dashboard redesign; no unrelated approval-policy refactor.
- Done when: AC1-AC5 are satisfied with targeted tests or explicit waiver.
- Expected evidence: dashboard tests/typecheck/lint, focused Python dashboard API test, code audit for related redirect/refresh controls.

## Context
- Thread: Investigate and implement consistent Telegram Business dashboard “Generate draft now” behavior.
- Slice: Single owned dashboard draft UX/API consistency slice; stayed whole.
- Task name: Telegram Business dashboard Generate draft now behavior
- Task package: `docs/plans/2026-05-26-telegram-business-media`
- Report path: `docs/plans/2026-05-26-telegram-business-media/reports/dashboard-draft-owner.md`
- Worktree: `/home/kcnc/code/hermes/hermes-agent`
- Branch: `main` in current checkout, per supplied worktree/branch instruction.
- Verify scope: targeted dashboard/app tests and focused backend dashboard API tests.
- Review target: local uncommitted diff in files listed below.

## Spec compliance
- AC1 no navigation/refresh/context loss: done.
  - Evidence: Generate button is `type="button"`; success path now uses `refreshDetailInPlace()` instead of `loadDetail()`, so ready detail state is not cleared/unmounted after request.
- AC2 queued/generating/result/error state: done.
  - Evidence: action alert titles distinguish `Generating draft`, `Draft request queued`, and `Action failed`; button label changes to `Queueing draft...` while action is loading.
- AC3 optional empty/non-empty prompt: done.
  - Evidence: client trims prompt and omits empty prompt; BFF forwards `prompt`; backend stores prompt in event metadata/channel context/history and response when non-empty.
- AC4 related redirect/refresh audit: done.
  - Evidence: no `<form` under dashboard source; Business dashboard buttons in `chat-detail-view.tsx` and `dashboard-view.tsx` now specify `type="button"`.
- AC5 targeted tests/checks: done.
  - Evidence: verification commands in `verification/dashboard-draft.md` passed, with noted environment retry.

## Acceptance verification
- AC1: Generate draft does not navigate away, refresh, or lose chat detail.
  - Covered by: code audit + component/API tests.
  - Result: passed.
  - Evidence: `npm run test:auth -- src/lib/business/business-api.test.ts src/app/api/business/route-handlers.test.ts src/components/business/business-dashboard-ui.test.tsx` passed (19 tests).
- AC2: State transition is visible.
  - Covered by: UI implementation and render test.
  - Result: passed.
  - Evidence: same targeted Vitest suite passed; loading/success/error titles and button label are present in code.
- AC3: Empty/non-empty prompt behavior works through API layers.
  - Covered by: Vitest client/BFF tests and Python dashboard API test.
  - Result: passed.
  - Evidence: targeted Vitest suite passed; `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py` passed (15 tests).
- AC4: Similar unintended redirect/refresh behavior audited.
  - Covered by: code audit (`grep` for `<form` and dashboard `Button` controls) and direct fixes.
  - Result: passed.
  - Evidence: no dashboard `<form`; explicit `type="button"` on Business dashboard controls.
- AC5: No obvious draft endpoint regression.
  - Covered by: `npm run typecheck`, `npm run lint`, targeted API tests.
  - Result: passed.
  - Evidence: commands passed as recorded below.

## System readiness
- Routes / registration: done; existing draft BFF route remains same path and forwards added optional field.
- Services / APIs: done; backend dashboard API accepts optional prompt while preserving `source: latest` validation.
- Config / env / secrets: not changed.
- Permissions / access: unchanged; Telegram initData and service bearer-token patterns preserved.
- Database / migrations: not relevant; JSON history normalization now preserves optional `prompt` text.
- Frontend-backend integration: done; client/BFF/backend tests cover prompt pass-through.
- Runtime / deployment wiring: not deployed by scope; ready for parent review/deploy.

## Verification run
- Local / targeted checks:
  - `cd apps/telegram-business-dashboard && npm run test:auth -- src/lib/business/business-api.test.ts src/app/api/business/route-handlers.test.ts src/components/business/business-dashboard-ui.test.tsx`: passed, 3 files / 19 tests.
  - `cd apps/telegram-business-dashboard && npm run typecheck`: passed.
  - `cd apps/telegram-business-dashboard && npm run lint`: passed.
  - `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py`: passed, 15 tests.
- Local / failed attempts:
  - `scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py -q`: failed before tests because per-file runner does not accept `-q`.
  - `scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py`: failed before tests because `.venv` lacks pytest; rerun with `HERMES_TEST_VENV=$PWD/venv` passed.
- Remote checks / CI:
  - Status: not available before push; no PR/push performed.

## Issues
### Issue R-01: Detail remounted/blanked after draft request
- Description: Draft success path called `loadDetail()`, which sets `status="loading"` and clears/replaces ready detail during refresh.
- Evidence: prior `handleGenerateDraft()` called `await loadDetail()` after success.
- Resolution: added `refreshDetailInPlace()` that refreshes detail/history without clearing mounted detail state.
- Depends on: none.

### Issue R-02: Prompt/topic was not accepted or forwarded
- Description: Generate draft client/BFF/backend only sent and accepted `{source:"latest"}`.
- Evidence: prior `generateBusinessDraft()` body and BFF whitelist had only `source`; backend `request_draft()` accepted only source/actor.
- Resolution: added optional prompt input, client trim/omit-empty behavior, BFF prompt forwarding, backend prompt metadata/channel context/history/response preservation, and tests.
- Depends on: none.

### Issue R-03: Button default-type ambiguity in dashboard controls
- Description: Business dashboard buttons did not consistently specify `type="button"`, leaving future form nesting vulnerable to accidental submit/navigation.
- Evidence: code audit found `Button` controls without `type` in `chat-detail-view.tsx` and `dashboard-view.tsx`; no `<form` currently exists.
- Resolution: set explicit `type="button"` on related Business dashboard controls.
- Depends on: none.

## Side findings
- Blocking findings folded into active work: R-01, R-02, R-03.
- Non-blocking findings tracked separately: none; no GitHub follow-up required.

## Changed files
- `apps/telegram-business-dashboard/src/components/business/chat-detail-shell.tsx`
- `apps/telegram-business-dashboard/src/components/business/chat-detail-view.tsx`
- `apps/telegram-business-dashboard/src/components/business/dashboard-view.tsx`
- `apps/telegram-business-dashboard/src/lib/business/api.ts`
- `apps/telegram-business-dashboard/src/lib/business/types.ts`
- `apps/telegram-business-dashboard/src/app/api/business/chats/[token]/draft/route.ts`
- `gateway/platforms/telegram_business_dashboard_api.py`
- `gateway/platforms/telegram_business_history.py`
- Tests: `apps/telegram-business-dashboard/src/lib/business/business-api.test.ts`, `apps/telegram-business-dashboard/src/app/api/business/route-handlers.test.ts`, `apps/telegram-business-dashboard/src/components/business/business-dashboard-ui.test.tsx`, `tests/gateway/test_telegram_business_dashboard_api.py`
- Task docs: `plan.md`, `verification/dashboard-draft.md`, this report.

## Verdict
- Status: success.
- Goal state: fully achieved locally for scoped implementation.
- Final readiness: ready for parent review/deploy; not deployed to VPS by scope.
- Summary: Dashboard draft generation is now an in-place action with visible status, optional prompt pass-through, explicit non-submit controls, and targeted passing tests.

## Next-agent brief
- Objective: Parent reviewer can inspect diff and deploy/restart on VPS if desired.
- Target: changed files above.
- Settled already: route/API contract remains `source: latest` plus optional `prompt`; empty prompt is omitted and remains valid.
- Boundaries: do not deploy from this slice report unless parent explicitly proceeds; avoid unrelated dashboard redesign.
- Verification target: rerun listed tests after any review changes; browser/live Web App check can be done during deployment validation.
- Expected output: review/deploy decision and any production runtime evidence if parent continues to VPS.

---

## Root owner integration addendum (2026-05-26)

### Integrated slice result
- Slice structure: kept as one dashboard draft UX/API consistency slice because the frontend detail UI, BFF route, and Python dashboard API share one acceptance story.
- Slice owner result: accepted locally; no VPS deploy performed.
- Acceptance audit: `reports/acceptance-auditor.md` accepted the local diff with the explicit limitation that live browser/VPS smoke is still required before claiming production rollout.

### Root verification rerun
- `cd apps/telegram-business-dashboard && npm run test:auth -- src/lib/business/business-api.test.ts src/app/api/business/route-handlers.test.ts src/components/business/business-dashboard-ui.test.tsx && npm run typecheck && npm run lint`
  - Result: passed (`3` Vitest files / `19` tests; typecheck and lint exited 0).
- `HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh tests/gateway/test_telegram_business_dashboard_api.py`
  - Result: passed (`15` tests).

### Root done-state
- Final status: locally complete / ready for parent review and deployment decision.
- Deployment: intentionally not performed.
- Remaining limitation: after deployment to `EverydayWiteVPS`, run a live Telegram Web App smoke test to confirm the in-place queued/generating/result UI with a real generated draft.
