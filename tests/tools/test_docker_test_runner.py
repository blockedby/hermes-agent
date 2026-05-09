"""Contract tests for the containerized local test runner."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE_TEST = REPO_ROOT / "Dockerfile.test"
COMPOSE_TEST = REPO_ROOT / "docker-compose.test.yml"
RUN_TESTS = REPO_ROOT / "scripts" / "run_tests.sh"
RUN_TESTS_DOCKER = REPO_ROOT / "scripts" / "run_tests_docker.sh"


def test_docker_test_image_tracks_ci_python_and_has_node() -> None:
    text = DOCKERFILE_TEST.read_text()

    assert "python3.11" in text
    assert "nodejs" in text
    assert "npm" in text
    assert "ripgrep" in text
    assert "--ignore-scripts" in text
    assert ".[all,dev]" in text


def test_docker_test_runner_uses_container_venv() -> None:
    run_tests = RUN_TESTS.read_text()
    docker_runner = RUN_TESTS_DOCKER.read_text()
    compose = COMPOSE_TEST.read_text()

    assert "HERMES_TEST_VENV" in run_tests
    assert "HERMES_TEST_VENV=/opt/hermes-test-venv" in docker_runner
    assert "Dockerfile.test" in docker_runner
    assert "Dockerfile.test" in compose
    assert "build-assets" in compose
