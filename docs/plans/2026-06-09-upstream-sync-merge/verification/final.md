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

## Containerized build attempts

- Full frontend/web/TUI build was not run. The full Docker test image could not complete dependency installation due registry/network failures above. No host npm/uv build/install/lock commands were run.
