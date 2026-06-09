# Plan — Hermes fork attribution + Telegram gateway evidence

## Task intake
Goal: add a public attribution file (`MY_CHANGES.md`) for blockedby's Hermes Agent fork work, focused on Telegram/business gateway improvements and related setup/config/test evidence.

In scope:
- Root-level or docs attribution markdown.
- Clear upstream attribution to NousResearch/upstream maintainers in the first 10 lines.
- Exact relevant fork/local commit hashes and GitHub links where possible.
- File/area summary and verification notes from repo evidence.
- Secret/overclaim-safe public wording.

Out of scope:
- Code behavior changes.
- Pulling/merging upstream/fork branches blindly.
- Raw logs, private runtime evidence, tokens/chat IDs/user data, or claims Alexander built Hermes Agent.

Done state:
- `MY_CHANGES.md` is added/updated and verified with git evidence, diff check, secret/overclaim scan, and status evidence.

Blocking unknowns:
- None for local docs creation. Push safety depends on remote/auth state.

## Repo orientation
- Repo root guidance: `AGENTS.md` says this checkout is a fork/work branch; do not blindly pull/merge remote tracking branch; prefer explicit comparisons.
- README attributes Hermes Agent to Nous Research/upstream.
- Relevant areas likely include `gateway/platforms/telegram.py`, `gateway/run.py`, `gateway/session.py`, `hermes_cli/config.py`, tests under `tests/gateway/` and `tests/hermes_cli/`.
- Verification commands requested: `git log`/`git diff origin/main...HEAD`, `git diff --check`, markdown secret/overclaim scan, `git status --short --branch`.

## Reuse discovery
- `AGENTS.md` already lists known local-only content commits and warns about duplicated remote-only hashes.
- Existing `README.md` establishes upstream branding language to preserve.
- Git history can provide exact commit/file evidence.

## Missing pieces
- Add `MY_CHANGES.md` with attribution, commit table, area summary, verification notes, and privacy statement.
- Verify changed markdown only for forbidden phrase, overclaims, and secret-like patterns.
- Record evidence in `verification/local.md` and final report.

## Plan tasks

### Task 1: Public attribution document
Goal:
- Create `MY_CHANGES.md` summarizing blockedby's fork changes without overclaiming upstream ownership.

Boundary:
- System area: repo docs/public attribution.
- Primary verification: markdown content inspection plus git evidence and secret/overclaim scan.

Existing pattern / reuse:
- Upstream attribution wording from `README.md` and commit evidence from git history.

Missing change:
- Root-level attribution markdown.

Scope / likely files:
- `MY_CHANGES.md`
- `docs/plans/2026-06-02-hermes-fork-attribution/*` for planning/report evidence.

Acceptance criteria:
- First 10 lines state upstream Hermes Agent is by NousResearch/upstream maintainers and this file summarizes blockedby's fork work.
- Exact relevant commits with hashes and GitHub links where possible.
- Touched file/area summary and verification notes based on repo evidence.
- No secrets/raw logs/private identifiers/forbidden public phrase/claim that Alexander built Hermes Agent.

Test plan:
- `git log --oneline origin/main..HEAD` or equivalent exact commit evidence.
- `git diff --stat origin/main...HEAD` / selected commit file evidence.
- `git diff --check`.
- `rg` scan over changed markdown for secret patterns, private data indicators, forbidden phrase, and overclaim wording.
- `git status --short --branch`.

Dependencies: none.
Executor candidate: `aad-implementer`.
Report path: `docs/plans/2026-06-02-hermes-fork-attribution/reports/aad-implementer-my-changes.md`.

## Dependency graph
- Task 1 can run immediately and stays whole under one implementer; no sub-slices needed.

## Execution ledger
- 2026-06-02: Slice owner created isolated worktree and task package. Status: implemented and locally verified. See `reports/aad-implementer-my-changes.md` and `verification/local.md`.


## Acceptance verification
- First 10 lines upstream attribution: passed (`verification/local.md`).
- Exact commits/links: passed (`MY_CHANGES.md` commit table; git log evidence in `verification/local.md`).
- Touched-area summary and verification notes: passed (`MY_CHANGES.md`).
- Safety/privacy/overclaim scan: passed (`verification/local.md`).
- `git diff --check`: passed (`verification/local.md`).
- Tests: not run; docs-only change, no code path changed.

## Final local done-state
- Slice stayed whole; direct implementation was completed because nested subagent dispatch was unavailable at current subagent depth.
- Current-goal blockers: none.
- Follow-ups: none.
