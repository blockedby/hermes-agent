# Final report — upstream sync/merge 2026-06-09

## Task
- Mission: Merge upstream `refs/remotes/hermes-origin-local/main` at `e88116256` into the local Hermes fork while preserving local fork changes.
- Target: `/home/kcnc/code/hermes/hermes-agent`.
- Boundaries: Tests/builds/locks/install/build commands were container-only; host-side git/read operations only. No assumption that live Hermes runs locally.
- Done when: upstream target is contained, local fork changes survive, conflict markers are gone, final branch is committed, verification evidence and risks are recorded.

## Context
- Task package: `docs/plans/2026-06-09-upstream-sync-merge`.
- Work branch: `sync/upstream-20260609`; integrated back to `main` with `git reset --hard sync/upstream-20260609` after confirming root checkout was clean.
- Final `main` HEAD: reporting commit `docs: record upstream sync verification` (see current `git log` for hash).
- Merge commit: `47cd74326156a2b577653d200ed8c98cbc40f53b` (`merge: sync upstream main`).
- Merge parents: `0f7802847` (local plan/sync branch) and `e88116256` (upstream target).
- Accidental checkpoint `b39b67f24`: dropped from finalized `main`; `git branch --contains b39b67f24` returned no branches.

## Slice structure used and why
- Slice A (CLI/update/install/deps/test-helper): kept at root-owner level for the small but cross-cutting `AGENTS.md`, `Dockerfile.test`, and `docker-compose.test.yml` resolutions.
- Slice B (Gateway/messaging/Telegram Business): delegated to `aad-slice-owner` because Telegram Business conflicts were behavior-heavy and needed focused preservation.
- Slice C (Agent/providers/tools): delegated to `aad-slice-owner` because Codex Responses/tool behavior had a separate test conflict and verification story.
- Slice D/E (Frontend/dashboard/docs/skills): integrated at root level because there were no textual conflicts after the merge; preservation was verified by git status/diff shape and final checks rather than code edits.

## Spec compliance
- AC1 upstream merged:
  - Status: done.
  - Evidence: `git rev-list --left-right --count HEAD...refs/remotes/hermes-origin-local/main` => `53 0`; final merge commit parent includes `e88116256`.
- AC2 accidental empty checkpoint handled:
  - Status: done.
  - Evidence: final branch starts from `32d3f0449` lineage via `0f7802847`; `b39b67f24` is not contained by any branch.
- AC3 local fork behavior preserved/adapted:
  - Status: partial but implemented.
  - Evidence: local Telegram Business modules and tests remain; Slice B report records retained approval drafts, business chat/session identity, direct-topic/thread fallback, dashboard API/history, media handling. Slice C report records retained Codex Responses empty-tools behavior and upstream xAI schema-sanitizer tests. Docker helpers remain with upstream workspace adaptation.
  - Gap: targeted pytest could not run because container dependency downloads repeatedly failed.
- AC4 conflicts resolved:
  - Status: done.
  - Evidence: no unmerged files; conflict-marker scan outside intentional tests/reports returned no output.
- AC5 container-only verification:
  - Status: partial.
  - Evidence: containerized tracked-Python AST parse passed; targeted Docker pytest attempts were containerized but blocked before pytest by network/dependency fetch failures. No host pytest/npm/uv build/install/lock commands were run.
- AC6 final report:
  - Status: done.
  - Evidence: this file and `verification/final.md`.

## Slice owner results integrated
- Gateway/Telegram report: `reports/slice-gateway-telegram.md` plus subagent output.
  - Outcome: resolved `gateway/platforms/telegram.py`, `gateway/run.py`, and `tests/gateway/test_send_image_file.py`; staged conflict resolutions; syntax check passed in container; pytest blocked by Docker build input/network issue.
- Agent/providers/tools report: `reports/slice-agent-providers-tools.md` plus subagent output.
  - Outcome: resolved `tests/run_agent/test_run_agent_codex_responses.py`; preserved local empty-tools coverage and upstream sanitizer/idempotence coverage; syntax check passed in container; pytest blocked by Docker dependency fetch issue.
- Root integration:
  - Resolved `AGENTS.md` by keeping upstream maxim plus local runtime-location warning.
  - Updated `Dockerfile.test` for upstream single root npm lock/workspaces and made Python test image skip npm workspace installation by default.
  - Updated `docker-compose.test.yml` so the `build-assets` service opts into npm dependency installation with `HERMES_DOCKER_INSTALL_NODE_DEPS=1`.
  - Committed merge and reset root `main` to the finalized merge branch.

## Verification run
- Container / syntax:
  - `docker run --rm -i -v "$PWD:/workspace:ro" -v /tmp/hermes_py_files_root.txt:/tmp/py_files:ro -w /workspace python:3.11-slim python - <<'PY' ... ast.parse tracked Python files ... PY`: passed, `AST checked 2206 tracked Python files`.
- Container / targeted pytest:
  - `scripts/run_tests_docker.sh ... -q`: blocked before pytest by external dependency fetch failures. See `verification/final.md`.
- Host git/read checks:
  - clean status, upstream contained (`53 0`), conflict-marker scan clean, accidental commit dropped.

## System readiness and risks
- Ready as a committed merge checkpoint: yes.
- Ready as fully test-validated: no; targeted pytest and frontend builds are not proven because container dependency installation could not complete due network/registry failures.
- Runtime risk: Telegram Business behavior was preserved by conflict resolution and syntax checks, but not exercised by pytest in this run.
- Build risk: npm workspace install for `build-assets` remains unproven after adapting to upstream root lockfile; it must be run in a container when network conditions allow.

## Changed files / commits
- Final reporting commit: `docs: record upstream sync verification` (current `HEAD`).
- Sync merge commit: `47cd74326 merge: sync upstream main`.
- Planning commit: `0f7802847 docs: plan upstream sync merge`.
- Upstream merged through: `e88116256 fix(update): scope git fetch to target branch`.
- Major local-resolution files: `AGENTS.md`, `Dockerfile.test`, `docker-compose.test.yml`, `gateway/platforms/telegram.py`, `gateway/run.py`, `tests/gateway/test_send_image_file.py`, `tests/run_agent/test_run_agent_codex_responses.py`, plus task package files under `docs/plans/2026-06-09-upstream-sync-merge/`.

## Issues
### R-01: Merge conflicts resolved
- Evidence: no unmerged paths; final merge commit created.
- Resolution: conflicts resolved preserving local Telegram Business/Codex/test-helper behavior and upstream refactors.

### R-02: Accidental checkpoint removed from branch lineage
- Evidence: `git branch --contains b39b67f24` returned no branches after resetting `main` to the sync branch.
- Resolution: final sync branch was based on `b39b67f24^` and does not retain the empty commit.

### U-01: Container dependency downloads blocked pytest/build validation
- Evidence: Docker test build failed fetching npm packages (`ERR_SOCKET_TIMEOUT`), then after skipping npm for Python tests failed fetching PyPI packages (`tqdm`, `agent-client-protocol`) with connection resets.
- Why unresolved: external network/registry instability during container build; user forbade host dependency/test/build runs.
- Needed next: retry `scripts/run_tests_docker.sh ... -q` when container network is stable; then run containerized build checks as needed.

## Acceptance audit
- `aad-acceptance-auditor` verdict: accepted with limitations.
- Auditor-confirmed: AC1, AC2, AC4, AC6 passed; AC3 partial because behavior was preserved by conflict resolution/syntax evidence but not runtime pytest; AC5 passed with limitation because verification attempts were container-only and blockers were recorded.
- Owner clarification: the initial Docker build-input blocker from removed per-workspace npm lockfiles was addressed by `Dockerfile.test`/`docker-compose.test.yml`; remaining pytest/build blocker is container dependency download/network failure during image construction.

## Follow-up container verification and fixes
- A narrower container-only targeted image (`hermes-agent:test-runner-targeted`, built from a temporary Dockerfile under `/tmp`) avoided the flaky `[google]` extra after full `[all,dev]` image builds repeatedly failed on external registry downloads.
- First targeted pytest run found a real merge regression in `gateway/run.py::_is_user_authorized`: `user_id` was referenced before assignment for Telegram Business authorization.
- Fixed by restoring `user_id = source.user_id`, guarding pairing-store lookup for no-user sources, and returning `False` for no-user sources after chat-scoped allowlist checks.
- Containerized focused rerun: `tests/gateway/test_telegram_business.py` => `76 tests passed, 0 failed`.
- Containerized targeted rerun: 11 files / `414 tests passed, 0 failed` covering Codex Responses, model tools/toolsets, image/transcription helpers, Telegram Business/dashboard/session/thread/send-image files.
- Full official Docker runner was retried again after the auth-policy fix, but still blocked before pytest by external dependency downloads (`pydantic-core`, then repeated `google-api-python-client` failures, including `peer closed connection without sending TLS close_notify`).
- Broad fallback full-discovery suite in the targeted image ran to completion: `1405 files, 29711 tests passed, 56 failed`. Because the image lacks full `[all,dev]`, ACP and some optional-dependency failures are expected fallback-image fallout, not authoritative full-suite failures.
- That broad fallback did expose additional real merge-regression gaps in the local `gateway/run.py` auth override. Restored upstream behavior for adapter `enforces_own_access_policy`, config-driven `dm_policy` unauthorized-DM behavior, and SimpleX display-name allowlist matching.
- Containerized focused rerun after those auth fixes: `tests/gateway/test_config_driven_access_policy.py`, `tests/gateway/test_unauthorized_dm_behavior.py`, `tests/gateway/test_telegram_business.py` => `3 files, 137 tests passed, 0 failed`.
- A later official full Docker runner succeeded in building the full `[all,dev]` image and ran pytest to completion: `42 files with test failures (85 tests failed)`. This replaced the prior registry blocker with real suite signal.
- Localized official-run failures were fixed for Docker test context and restart/update contracts: include repo docs/CI metadata in the image, create a lightweight `.git` in `Dockerfile.test`, mask Docker markers in restart tests that assert the non-container path, and support both `gateway.run.__file__` and `gateway.slash_commands.__file__` project-root patching in `/update` after slash-command extraction.
- Containerized focused rerun after those official-run fixes: 8 files / `223 tests passed, 0 failed` covering restart drain/notification, gateway update command/streaming, CLI update/autostash, lint workflow metadata, and Windows README checks.

## Verdict
- Status: successful targeted/focused verification with limitations.
- Goal state: upstream merge completed and committed; local changes intentionally preserved; targeted runtime tests, auth-policy focused tests, and focused official-failure regression tests pass in containers after merge-regression/test-image fixes.
- Remaining limitation: official full `[all,dev]` Docker suite is no longer blocked by image construction, but the latest full run still had `42 files with test failures (85 tests failed)`, many involving 30s timeouts around lazy dependency installs/subprocess waits and container/root environment assumptions. These remaining failures are not yet fully classified as merge regressions. Frontend/web/TUI builds remain unproven. No host pytest/npm/uv/build/install commands were run.

## Next-agent brief
- Objective: complete official full verification and classify remaining full-suite failures.
- Target: same current `main` `HEAD`.
- Settled: do not reintroduce `b39b67f24`; upstream target is already merged; conflicts are resolved; targeted Python runtime suite and auth-policy focused suite pass in containers after the `gateway/run.py` fixes.
- Boundaries: continue honoring container-only tests/builds/locks.
- Verification target: rerun official `scripts/run_tests_docker.sh` after the Docker test-context/update/restart fixes; classify/fix only current-goal regressions; run containerized frontend/dashboard/TUI build checks when practical.
