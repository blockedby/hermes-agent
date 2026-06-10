# Task 6 invocation policy progress

- 2026-06-10: Started in `/tmp/pi-worktree-78ff96c3-0` on branch `pi-parallel-78ff96c3-0`; root `AGENTS.md` and plan loaded. Initial `git status --short` clean.
- 2026-06-10: Added RED tests for invocation policy off/draft/direct, configured username matching, slash-with-mention blocking, and one-shot direct metadata routing.
- 2026-06-10: RED container check failed as expected: `tests/gateway/test_telegram_business.py -q -k 'mention or invocation or slash'` had 2 failing new mention policy tests (watch notification happened instead of mention_draft/direct enqueue).
- 2026-06-10: Implemented profile-backed mention invocation routing and one-shot `business_mode` metadata propagation. Targeted container check passed: 16 selected tests.
- 2026-06-10: Broader touched-file container test passed: `tests/gateway/test_telegram_business.py -- -q` reported 107 passed.
- 2026-06-10: Container `py_compile` and `ruff check` passed for touched Python files. Verification artifact written to `verification/task6-invocation-policy.md`.
- 2026-06-10: Committed implementation as `b22ec789b feat(telegram-business): add mention invocation policy`; committed report copy as `222284502 docs: add task6 invocation policy report`.
