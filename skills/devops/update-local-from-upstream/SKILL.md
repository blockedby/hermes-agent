---
name: update-local-from-upstream
description: Safely sync local changes from upstream.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    category: devops
    tags: [git, testing, upstream, synchronization]
---

# Update Local From Upstream Skill

Use this skill when you need to compare a local Hermes fork with upstream, merge new upstream commits, and prove whether regressions came from local changes or upstream drift. It does not replace project-specific release policy, pull-request review, or secret-handling rules.

## When to Use

- You maintain a local/private fork and need to pull in new upstream commits deliberately.
- You need before-and-after test evidence from both the private fork and an adjacent upstream clone.
- You need to identify regressions introduced by an upstream merge and fix them before reporting readiness.

## Prerequisites

- A clean or intentionally documented local working tree.
- A configured upstream remote, plus any private fork remote needed for comparison.
- An adjacent upstream clone when available, commonly `../hermes-agent-origin`.
- The repo's test runner, especially `scripts/run_tests.sh`.
- Native Hermes tools: `terminal` for commands, `read_file` for plans and logs, `write_file` for reports, and `search_files` for locating tests or guidance.

## How to Run

1. Use `terminal` to inspect local status and remotes before changing anything.
2. Use `terminal` to inspect the adjacent upstream clone status without overwriting dirty files.
3. Start full-suite tests for the private fork and upstream clone when time and machine capacity allow; they may run in parallel.
4. Fetch upstream safely, inspect incoming commits and duplicate-patch hazards, then merge or backport only after the evidence is clear.
5. Rerun tests after the merge/backport, fix current-goal regressions, and report exact commands and outcomes.

## Quick Reference

| Step | Command pattern |
| --- | --- |
| Local status | `git status --short --branch` |
| Remote summary | `git remote -v && git rev-list --left-right --count HEAD...origin/main` |
| Upstream clone status | `(cd ../hermes-agent-origin && git status --short --branch)` |
| Local full suite | `scripts/run_tests.sh` |
| Adjacent upstream suite | `(cd ../hermes-agent-origin && scripts/run_tests.sh)` |
| Fetch only | `git fetch origin main --no-tags` |
| Inspect incoming commits | `git log --oneline --left-right --cherry-pick HEAD...origin/main` |

## Procedure

1. Establish the baseline.
   - Run `git status --short --branch` in the local fork.
   - Record the active branch, dirty files, and upstream divergence.
   - If the local tree is dirty, decide whether the changes are in scope before continuing.

2. Inspect the adjacent upstream clone.
   - Run read-only status and divergence commands inside `../hermes-agent-origin`.
   - Do not run cleanup, reset, stash, or pull in that clone unless the user explicitly authorizes it.
   - If it is dirty, record the dirty paths and treat full-suite results as potentially affected by local clone edits.

3. Capture pre-merge test evidence.
   - Run `scripts/run_tests.sh` in the private fork.
   - Run `scripts/run_tests.sh` in the adjacent upstream clone if feasible.
   - Run the two suites in parallel only when CPU, disk, and isolation capacity are sufficient.
   - Save command lines, start/end status, exit codes, and log paths.

4. Inspect upstream before merging.
   - Fetch with `git fetch`, not `git pull`.
   - Review incoming commits with cherry-pick-aware comparisons to avoid duplicating local patches with different hashes.
   - Check known local-only commits and remote-only commits before accepting merge content.

5. Merge or backport deliberately.
   - Prefer a normal merge only when the local branch is meant to absorb all fetched upstream commits.
   - Prefer a backport/cherry-pick/manual patch when the task requests a narrow fix.
   - Resolve conflicts by preserving local intentional behavior and upstream fixes.

6. Rerun regression tests.
   - Run targeted tests for touched areas first.
   - Run `scripts/run_tests.sh` again for full-suite evidence when feasible.
   - Compare failures against the pre-merge fork and upstream-clone baselines.

7. Fix and classify findings.
   - Fix current-goal regressions before reporting readiness.
   - Record unrelated failures as follow-ups with enough evidence to reproduce.
   - Never hide failed or skipped full-suite attempts.

8. Report.
   - Include changed commit range, merge/backport method, tests run, failures, fixes, and remaining risks.
   - Note dirty upstream-clone state and duplicate-patch checks.
   - State whether the local fork is ready for the intended deployment or needs more work.

## Pitfalls

- Do not blindly run `git pull`; it can merge duplicate-patch commits or overwrite local intent.
- Do not reset or clean the adjacent upstream clone when it has dirty or untracked files.
- Do not claim full-suite success unless `scripts/run_tests.sh` completed successfully.
- Do not expose API keys, tokens, `.env` values, or private remote URLs in reports.
- Do not treat upstream-clone failures as local regressions until both baselines are compared.

## Verification

- Confirm the local report lists exact commands and exit codes.
- Confirm full-suite status is honest: passed, failed, running, skipped for time, or blocked by dirty clone state.
- Confirm duplicate-patch hazards were checked before any merge.
- Confirm current-goal regressions were fixed or clearly marked unresolved.
