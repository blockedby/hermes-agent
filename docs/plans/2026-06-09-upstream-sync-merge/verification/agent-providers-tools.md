# Verification — Slice C agent/providers/tools

## Acceptance verification

- AC1: `tests/run_agent/test_run_agent_codex_responses.py` has no conflict markers and retains upstream + local coverage.
  - Result: passed for conflict-marker/syntax checks; pytest not run.
  - Evidence:
    - `git grep -n "<<<<<<<\\|=======\\|>>>>>>>" -- tests/run_agent/test_run_agent_codex_responses.py run_agent.py agent/codex_responses_adapter.py agent/codex_runtime.py agent/message_sanitization.py agent/tool_executor.py model_tools.py tools/read_image_tool.py tools/transcription_tools.py tools/vision_tools.py toolsets.py` found no conflict markers in the conflict file; matches in other files were separator comments only.
    - Container AST check passed for `tests/run_agent/test_run_agent_codex_responses.py` and related agent/tool files.

- AC2: Local Codex/image/transcription/read-image behavior is not dropped.
  - Result: partial/pass by merge inspection; targeted pytest blocked.
  - Evidence: conflict resolution kept local `test_build_api_kwargs_codex_responses_omits_tools_when_empty` and upstream xAI schema-sanitization tests. Related files were not edited by this slice.

- AC3: Syntax/imports are coherent for changed agent/tool files.
  - Result: passed for syntax.
  - Evidence: container command below passed.

- AC4: Containerized targeted tests are run if feasible; otherwise document blocker.
  - Result: blocked.
  - Evidence: `scripts/run_tests_docker.sh tests/run_agent/test_run_agent_codex_responses.py tests/test_codex_responses_adapter.py tests/test_model_tools.py tests/test_toolsets.py tests/tools/test_read_image_tool.py tests/tools/test_transcription_tools.py -q` failed during Docker build before pytest because `Dockerfile.test` tries to copy missing `web/package-lock.json` and `ui-tui/package-lock.json`.

## Commands

```bash
scripts/run_tests_docker.sh tests/run_agent/test_run_agent_codex_responses.py tests/test_codex_responses_adapter.py tests/test_model_tools.py tests/test_toolsets.py tests/tools/test_read_image_tool.py tests/tools/test_transcription_tools.py -q
# Result: blocked during Docker build:
# ERROR: failed to calculate checksum ... "/ui-tui/package-lock.json": not found
# ERROR: failed to calculate checksum ... "/web/package-lock.json": not found
```

```bash
docker run --rm -i -v "$PWD:/workspace:ro" -w /workspace python:3.11-slim python - <<'PY'
import ast
from pathlib import Path
for file in ['tests/run_agent/test_run_agent_codex_responses.py','run_agent.py','agent/codex_responses_adapter.py','agent/codex_runtime.py','agent/message_sanitization.py','agent/tool_executor.py','model_tools.py','tools/read_image_tool.py','tools/transcription_tools.py','tools/vision_tools.py','toolsets.py']:
    ast.parse(Path(file).read_text(), filename=file)
    print(f'AST OK {file}')
PY
# Result: passed; all listed files reported AST OK.
```

Note: an owner-side host `ast.parse` was accidentally run before the container check; it is not used as acceptance evidence. The accepted syntax evidence is the containerized command above.
