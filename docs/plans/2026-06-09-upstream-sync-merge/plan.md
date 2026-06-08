# Plan: Upstream sync/merge 2026-06-09

## Intake

Goal: merge upstream `hermes-origin-local/main` (`e88116256 fix(update): scope git fetch to target branch`) into the local Hermes fork while preserving intentional local fork changes, especially Telegram Business approval/session/topic/dashboard work and local Codex/STT/test-runner compatibility.

Known starting state:
- Root checkout: `/home/kcnc/code/hermes/hermes-agent` on `main` at `b39b67f24`.
- `b39b67f24` is an accidental empty checkpoint commit. This work branch starts from its parent `32d3f0449`, effectively dropping the empty checkpoint from the sync result.
- Merge-base with upstream: `2d5dcfabc`.
- Work branch divergence at creation: local `51` commits ahead, upstream `1338` commits ahead.
- Dry-run merge conflicts: `AGENTS.md`, `gateway/platforms/telegram.py`, `gateway/run.py`, `tests/gateway/test_send_image_file.py`, `tests/run_agent/test_run_agent_codex_responses.py`.

Hard constraints:
- Host-side read/git operations are allowed.
- All tests, builds, npm/uv lock/install/build, and similar verification must run inside containers only.
- Do not assume the live Hermes runtime is local.
- Preserve local changes over upstream when resolving conflicts unless an upstream refactor requires adapting the local behavior.

## Acceptance criteria

AC1. Upstream `hermes-origin-local/main` is merged into the local fork work branch with a coherent merge commit or clearly documented checkpoint if incomplete.
AC2. The accidental empty checkpoint commit `b39b67f24` is not retained in the final sync branch unless explicitly justified.
AC3. Local fork behavior is preserved/adapted, especially Telegram Business approval/session/topic/dashboard behavior, local Codex Responses hardening, local STT endpoint compatibility, Docker test helper compatibility, and documented local fork guidance.
AC4. Conflicts are resolved without conflict markers and with imports/routes/tests adjusted to current upstream structure.
AC5. Verification is container-only, with exact commands and results recorded. Targeted tests cover conflict-heavy areas; broader build/test evidence is run when feasible or honestly reported as blocked/partial.
AC6. Final report lists changed files/commits, verification, unresolved risks, and continuation plan if not complete.

## Slice structure and execution waves

### Slice A: CLI/update/install/deps/test-helper integration
Goal: Preserve local Docker test helpers, local update-from-upstream skill/guidance, dependency pinning/test runner compatibility, and adapt to upstream install/update changes.
Likely files: `.dockerignore`, `.gitignore`, `Dockerfile.test`, `docker-compose.test.yml`, `scripts/run_tests*.sh`, `scripts/build_docker.sh`, `skills/devops/update-local-from-upstream/SKILL.md`, `AGENTS.md`, dependency manifests if needed.
Acceptance: local helper files survive the merge; containerized test script remains executable and points tests into `/opt/hermes-test-venv`; no host lock/build commands used.
Verification: host git checks only plus container smoke/targeted checks using `scripts/run_tests_docker.sh` or `docker compose -f docker-compose.test.yml run --rm ...`.
Depends on: root merge state. Can run parallel with B/C/D/E only as read/recommendation; implementation must serialize in shared merge worktree.
Report path: `reports/slice-cli-update-install.md`.

### Slice B: Gateway/messaging/Telegram Business integration
Goal: Resolve/validate Telegram gateway conflicts and preserve local Telegram Business approval drafts, session isolation, direct-topic fallback, dashboard API, history/context, and media behavior across upstream gateway refactors.
Likely files: `gateway/platforms/telegram.py`, `gateway/run.py`, `gateway/session.py`, `gateway/config.py`, `gateway/platforms/telegram_business_*.py`, `tests/gateway/test_telegram*.py`, `tests/gateway/test_session*.py`, docs.
Acceptance: no conflict markers; local Telegram Business APIs and commands remain wired; upstream gateway refactors/imports are respected; existing local tests still target valid symbols.
Verification: containerized targeted gateway tests, especially `tests/gateway/test_telegram_business.py`, `tests/gateway/test_telegram_business_dashboard_api.py`, `tests/gateway/test_telegram_session_isolation.py`, `tests/gateway/test_telegram_thread_fallback.py`, `tests/gateway/test_send_image_file.py`.
Depends on: root merge state. Blocks final verification.
Report path: `reports/slice-gateway-telegram.md`.

### Slice C: Agent/providers/tools integration
Goal: Preserve local Codex Responses/media/tool hardening while adapting to upstream agent/provider refactors.
Likely files: `run_agent.py`, `agent/*codex*`, `agent/message_sanitization.py`, `agent/tool_executor.py`, `model_tools.py`, `tools/read_image_tool.py`, `tools/transcription_tools.py`, `tools/vision_tools.py`, `toolsets.py`, related tests.
Acceptance: local Codex Responses image/tool behavior and transcription/read-image compatibility survive; tests reference current upstream APIs.
Verification: containerized targeted tests including `tests/run_agent/test_run_agent_codex_responses.py`, `tests/test_codex_responses_adapter.py`, `tests/test_model_tools.py`, `tests/test_toolsets.py`, `tests/tools/test_read_image_tool.py`, `tests/tools/test_transcription_tools.py`.
Depends on: root merge state. Blocks final verification.
Report path: `reports/slice-agent-providers-tools.md`.

### Slice D: Frontend/desktop/TUI/dashboard integration
Goal: Preserve local `apps/telegram-business-dashboard` while accepting upstream desktop/TUI/dashboard additions and not rebuilding the chat surface outside Ink.
Likely files: `apps/telegram-business-dashboard/**`, `apps/desktop/**`, `ui-tui/**`, `web/**`, package manifests.
Acceptance: local dashboard app remains present with its AGENTS constraints; upstream desktop/TUI changes are not overwritten by local dashboard additions; package/test commands are containerized only.
Verification: containerized npm tests/builds if feasible, e.g. via Docker test image commands for dashboard tests and upstream `ui-tui`/web build checks. No host npm commands.
Depends on: root merge state. Can mostly run after merge.
Report path: `reports/slice-frontend-dashboard.md`.

### Slice E: Skills/plugins/docs/release integration
Goal: Preserve local docs/plans and Telegram Business docs while accepting upstream docs/skills/plugins/release churn and ensuring no generated/secret pollution.
Likely files: `docs/**`, `website/**`, `skills/**`, `optional-skills/**`, `plugins/**`, release docs.
Acceptance: local task packages/docs remain; upstream docs additions retained; new task package updated; no secrets; no accidental host artifacts.
Verification: conflict-marker scan, documentation path checks, containerized doc/site build only if feasible.
Depends on: root merge state. Blocks final report only if conflicts/overlaps found.
Report path: `reports/slice-docs-skills.md`.

## Execution ledger

- 2026-06-09: Root owner created isolated worktree branch `sync/upstream-20260609` from `32d3f0449` to drop accidental empty checkpoint `b39b67f24` from the candidate sync branch.
- 2026-06-09: Dry-run `git merge-tree --messages HEAD refs/remotes/hermes-origin-local/main` found five textual conflicts: `AGENTS.md`, `gateway/platforms/telegram.py`, `gateway/run.py`, `tests/gateway/test_send_image_file.py`, `tests/run_agent/test_run_agent_codex_responses.py`.
