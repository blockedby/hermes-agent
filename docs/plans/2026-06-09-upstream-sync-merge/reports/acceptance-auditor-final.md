## Task package
- Task name: Upstream sync/merge 2026-06-09
- Task package: `docs/plans/2026-06-09-upstream-sync-merge`
- Report path: `docs/plans/2026-06-09-upstream-sync-merge/reports/acceptance-auditor-final.md`
- Acceptance plan path: `docs/plans/2026-06-09-upstream-sync-merge/verification/acceptance-plan.md`

## Acceptance verdict
- Status: accepted with limitations
- Summary: The merge is complete, conflict-free, and documented; the remaining limitation is that containerized targeted pytest/build validation was blocked by missing Docker build inputs, so runtime behavior is not fully exercised.

## Acceptance coverage
- AC1: Upstream `hermes-origin-local/main` is merged into the local fork work branch with a coherent merge commit or clearly documented checkpoint if incomplete.
  - Evidence present: `final-report.md`, `verification/final.md`
  - Result: passed
  - Gap: none
- AC2: The accidental empty checkpoint commit `b39b67f24` is not retained in the final sync branch unless explicitly justified.
  - Evidence present: `final-report.md`, `verification/final.md`
  - Result: passed
  - Gap: none
- AC3: Local fork behavior is preserved/adapted, especially Telegram Business approval/session/topic/dashboard behavior, local Codex Responses hardening, local STT endpoint compatibility, Docker test helper compatibility, and documented local fork guidance.
  - Evidence present: slice reports + final report
  - Result: partial
  - Gap: preserved behavior is supported by merge inspection, syntax checks, and retained tests/code paths, but targeted container pytest did not run; Telegram/Codex runtime behavior and STT compatibility are not fully exercised.
- AC4: Conflicts are resolved without conflict markers and with imports/routes/tests adjusted to current upstream structure.
  - Evidence present: `verification/final.md`, `verification/gateway-telegram.md`, `verification/agent-providers-tools.md`
  - Result: passed
  - Gap: none
- AC5: Verification is container-only, with exact commands and results recorded. Targeted tests cover conflict-heavy areas; broader build/test evidence is run when feasible or honestly reported as blocked/partial.
  - Evidence present: `verification/final.md`, `verification/gateway-telegram.md`, `verification/agent-providers-tools.md`
  - Result: passed with limitation
  - Gap: commands are container-only and the blocker is recorded, but the targeted pytest commands never reached pytest because Docker build failed on missing `web/package-lock.json` and `ui-tui/package-lock.json`.
- AC6: Final report lists changed files/commits, verification, unresolved risks, and continuation plan if not complete.
  - Evidence present: `final-report.md`
  - Result: passed
  - Gap: none

## System readiness coverage
- Routes / registration: covered at syntax/conflict level; runtime dispatch not exercised end-to-end.
- Services / APIs: partial; Telegram gateway behavior is preserved in reports, but container pytest did not run.
- Config / env / secrets: not relevant.
- Docker / containers: blocked; `Dockerfile.test`/lockfile mismatch prevented targeted container pytest.
- Permissions / access: not relevant.
- Database / migrations: not relevant.
- Frontend-backend integration: missing; frontend/container build checks were not completed.
- Runtime / deployment wiring: partial/unclear; merge and Dockerfile changes are documented, but not fully exercised.

## Check freshness
- Targeted checks: fresh but blocked
- Full local checks: missing
- Remote checks / CI: not available before push

## Required before done
- No blocker to accept the merge checkpoint itself.
- To retire the limitation, restore/adapt the Docker build inputs (`web/package-lock.json`, `ui-tui/package-lock.json`, or `Dockerfile.test` expectations) and rerun the containerized targeted pytest suites for the Telegram and Codex slices.

## Files written
- `docs/plans/2026-06-09-upstream-sync-merge/verification/acceptance-plan.md`: created
- `docs/plans/2026-06-09-upstream-sync-merge/reports/acceptance-auditor-final.md`: created
