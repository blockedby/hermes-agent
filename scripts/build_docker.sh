#!/usr/bin/env bash
# Build the production Hermes Docker image locally.
#
# Usage:
#   scripts/build_docker.sh
#   HERMES_DOCKER_IMAGE=hermes-agent:my-tag scripts/build_docker.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE="${HERMES_DOCKER_IMAGE:-hermes-agent:local}"
DOCKER_BIN="${DOCKER:-docker}"

exec "$DOCKER_BIN" build \
  -f "$REPO_ROOT/Dockerfile" \
  -t "$IMAGE" \
  "$REPO_ROOT"
