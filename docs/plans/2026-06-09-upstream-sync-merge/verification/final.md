# Final verification — upstream sync merge

All verification/build/test commands below were run in containers only, except host-side git/read/status commands.

## Git/read checks

- `git status --short --branch`
  - Result: clean after final report commit.
  - Evidence: `## main...origin/main [ahead 1392]` with no dirty paths.
- `git rev-list --left-right --count HEAD...refs/remotes/hermes-origin-local/main`
  - Result after final report commit: `54 0`; upstream target is fully contained.
- `git show --no-patch --pretty='%H%nParents: %P%nSubject: %s' HEAD`
  - Result: merge commit `47cd74326156a2b577653d200ed8c98cbc40f53b`, parents `0f7802847...` and `e88116256...`.
- `git branch --contains b39b67f24`
  - Result: no branches listed; accidental empty checkpoint commit was dropped from the finalized `main` branch.
- `git grep -n '<<<<<<<\|>>>>>>>' -- ':!docs/plans/2026-06-09-upstream-sync-merge/**' ':!tests/hermes_cli/test_update_post_pull_syntax_guard.py'`
  - Result: no output; no merge conflict markers outside the task package report command examples and intentional syntax-guard tests.

## Containerized checks

- `docker run --rm -i -v "$PWD:/workspace:ro" -v /tmp/hermes_py_files_root.txt:/tmp/py_files:ro -w /workspace python:3.11-slim python - <<'PY' ... ast.parse tracked Python files ... PY`
  - Result: passed.
  - Evidence: `AST checked 2206 tracked Python files`.

## Containerized targeted pytest attempts

- `scripts/run_tests_docker.sh tests/run_agent/test_run_agent_codex_responses.py tests/test_codex_responses_adapter.py tests/test_model_tools.py tests/test_toolsets.py tests/tools/test_read_image_tool.py tests/tools/test_transcription_tools.py tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_session_isolation.py tests/gateway/test_telegram_thread_fallback.py tests/gateway/test_send_image_file.py -q`
  - Result: blocked before pytest by container dependency downloads.
  - Attempt 1 evidence: Docker build reached npm workspace install and failed with `npm ERR! code ERR_SOCKET_TIMEOUT`.
  - Mitigation: updated `Dockerfile.test` to default-skip npm workspace install for Python test images; `docker-compose.test.yml` keeps `HERMES_DOCKER_INSTALL_NODE_DEPS=1` for `build-assets`.
  - Attempt 2 evidence: Docker build skipped npm install, then `uv pip install -e ".[all,dev]"` failed fetching `tqdm==4.68.1` from PyPI with connection reset.
  - Attempt 3 evidence: retry failed fetching `agent-client-protocol==0.9.0` from PyPI with connection reset.

## Containerized follow-up after initial report

- Built a narrower container-only targeted Python test image after the full `[all,dev]` image kept failing on external registry downloads:
  - `DOCKER_BUILDKIT=1 docker build -f /tmp/Dockerfile.hermes-targeted -t hermes-agent:test-runner-targeted .`
  - The temporary Dockerfile installed `.[dev,messaging,web]` inside the image and avoided the flaky `[google]` extra that repeatedly failed fetching `google-api-python-client`.
  - Result: passed image build; no host Python/npm/uv install was run.
- First targeted pytest run in that image found a real merge regression:
  - `tests/gateway/test_telegram_business.py::test_business_customer_bypasses_generic_dm_allowlist`
  - Failure: `NameError: name 'user_id' is not defined` in `gateway/run.py::_is_user_authorized`.
  - Fix: restored `user_id = source.user_id`, guarded pairing-store lookup when `user_id` is absent, and returned `False` for no-user sources after chat-scoped allowlist checks.
- Containerized focused rerun after the fix:
  - `docker run --rm -v "$PWD:/host:ro" ... hermes-agent:test-runner-targeted bash -lc 'rm -rf /tmp/workspace && cp -a /host /tmp/workspace && cd /tmp/workspace && scripts/run_tests.sh tests/gateway/test_telegram_business.py -- -q'`
  - Result: `76 tests passed, 0 failed`.
- Containerized targeted rerun after the fix:
  - `docker run --rm -v "$PWD:/host:ro" ... hermes-agent:test-runner-targeted bash -lc 'rm -rf /tmp/workspace && cp -a /host /tmp/workspace && cd /tmp/workspace && scripts/run_tests.sh tests/run_agent/test_run_agent_codex_responses.py tests/test_codex_responses_adapter.py tests/test_model_tools.py tests/test_toolsets.py tests/tools/test_read_image_tool.py tests/tools/test_transcription_tools.py tests/gateway/test_telegram_business.py tests/gateway/test_telegram_business_dashboard_api.py tests/gateway/test_telegram_session_isolation.py tests/gateway/test_telegram_thread_fallback.py tests/gateway/test_send_image_file.py -- -q'`
  - Result: `11 files, 414 tests passed, 0 failed`.

## Containerized full-suite attempts after targeted pass

- Official full Docker runner:
  - `HERMES_TEST_WORKERS=4 scripts/run_tests_docker.sh`
  - Result: blocked before pytest during Docker image build.
  - Evidence: `uv pip install -e ".[all,dev]"` failed fetching `https://pypi.org/simple/pydantic-core/` with `connection reset`.
- Official full Docker runner retry after auth-policy fix:
  - `HERMES_TEST_WORKERS=4 scripts/run_tests_docker.sh`
  - Result: still blocked before pytest during Docker image build.
  - Evidence: `uv pip install -e ".[all,dev]"` failed fetching `https://pypi.org/simple/google-api-python-client/` with `peer closed connection without sending TLS close_notify`.
- Full-cache retry image:
  - `DOCKER_BUILDKIT=1 docker build -f /tmp/Dockerfile.hermes-full-cache -t hermes-agent:test-runner-full-cache .`
  - Result: blocked before pytest during Docker image build.
  - Evidence: Debian apt layer eventually completed after mirror warnings, but `[all,dev]` install failed downloading/extracting `google-api-python-client==2.194.0` due network timeout.
- Broad fallback suite in the previously-built targeted image:
  - `docker run --rm -v "$PWD:/host:ro" ... hermes-agent:test-runner-targeted bash -lc 'rm -rf /tmp/workspace && cp -a /host /tmp/workspace && cd /tmp/workspace && scripts/run_tests.sh -j 4'`
  - Caveat: image contains `.[dev,messaging,web]`, not full `[all,dev]`; ACP/google/other optional-dependency failures are not authoritative full-suite failures.
  - Result: `1405 files, 29711 tests passed, 56 failed`.
  - Expected fallback-image fallout included `ModuleNotFoundError: No module named 'acp'` for ACP tests and timeout/import fallout from missing optional/full-image capabilities.
  - Useful signal: the broad fallback run exposed real merge-regression coverage gaps in `gateway/run.py` around config-driven adapter access policy and SimpleX display-name allowlists.
- Focused container rerun after restoring upstream auth-policy behavior into the local `gateway/run.py` override:
  - `docker run --rm -v "$PWD:/host:ro" ... hermes-agent:test-runner-targeted bash -lc 'rm -rf /tmp/workspace && cp -a /host /tmp/workspace && cd /tmp/workspace && scripts/run_tests.sh tests/gateway/test_config_driven_access_policy.py tests/gateway/test_unauthorized_dm_behavior.py tests/gateway/test_telegram_business.py -- -q'`
  - Result: `3 files, 137 tests passed, 0 failed`.
  - Fixes covered: adapter `enforces_own_access_policy` trust path, `dm_policy` unauthorized-DM behavior, SimpleX `SIMPLEX_ALLOWED_USERS` display-name matching, and Telegram Business authorization bypass.
- Official full Docker runner after registry recovered:
  - `HERMES_TEST_WORKERS=4 scripts/run_tests_docker.sh`
  - Result: Docker image built successfully and pytest ran to completion; `42 files with test failures (85 tests failed)`.
  - Useful signal: no missing `acp` fallback-image errors remained; the run exposed Docker-test-context issues (`.gitignore`, `.github`, `README.md`, and `.git` absent from image), restart tests that needed to explicitly mask Docker markers when asserting non-container behavior, and gateway update project-root compatibility after slash-command extraction.
  - Remaining non-localized failures were mostly 30s timeouts around lazy dependency installs / subprocess waits, container/root environment assumptions, and existing broad-suite instability; they are not yet all classified as merge regressions.
- Focused container rerun after fixing the localized official-run failures:
  - `docker run --rm -v "$PWD:/host:ro" ... hermes-agent:test-runner bash -lc 'rm -rf /tmp/workspace && cp -a /host /tmp/workspace && cd /tmp/workspace && scripts/run_tests.sh tests/gateway/test_restart_drain.py tests/gateway/test_restart_notification.py tests/gateway/test_update_command.py tests/gateway/test_update_streaming.py tests/hermes_cli/test_cmd_update.py tests/hermes_cli/test_update_autostash.py tests/test_lint_config.py tests/tools/test_windows_native_support.py -- -q'`
  - Result: `8 files, 223 tests passed, 0 failed`.
  - Fixes covered: Docker test context now includes repo docs/CI metadata and creates a lightweight `.git`; restart non-container assertions mask Docker markers; gateway `/update` supports both `gateway.run.__file__` and `gateway.slash_commands.__file__` project-root patching contracts.

## Containerized build attempts

- Full frontend/web/TUI build was not run. The full Docker test image could not complete dependency installation due registry/network failures above. No host npm/uv build/install/lock commands were run.
