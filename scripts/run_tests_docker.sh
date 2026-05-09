#!/usr/bin/env bash
# Run Hermes tests inside a Docker image instead of the host checkout.
#
# Usage:
#   scripts/run_tests_docker.sh                         # full non-e2e suite
#   scripts/run_tests_docker.sh tests/agent/ -q         # pass pytest args through
#   HERMES_DOCKER_BUILD=0 scripts/run_tests_docker.sh   # reuse existing image
#
# This builds Dockerfile.test, then runs scripts/run_tests.sh inside the image.
# The source is copied into the image at build time rather than bind-mounted,
# so host venvs/systemd/HERMES_HOME cannot leak into the test process.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE="${HERMES_DOCKER_TEST_IMAGE:-hermes-agent:test-runner}"
DOCKERFILE="${HERMES_DOCKER_TEST_FILE:-Dockerfile.test}"
DOCKER_BIN="${DOCKER:-docker}"

if [ "${HERMES_DOCKER_BUILD:-1}" != "0" ]; then
  "$DOCKER_BIN" build \
    -f "$REPO_ROOT/$DOCKERFILE" \
    -t "$IMAGE" \
    "$REPO_ROOT"
fi

exec "$DOCKER_BIN" run --rm \
  -e HERMES_TEST_VENV=/opt/hermes-test-venv \
  -e HERMES_TEST_WORKERS="${HERMES_TEST_WORKERS:-4}" \
  -e TZ=UTC \
  -e LANG=C.UTF-8 \
  -e LC_ALL=C.UTF-8 \
  -e PYTHONHASHSEED=0 \
  "$IMAGE" \
  scripts/run_tests.sh "$@"
