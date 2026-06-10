## Task
- Mission: Implement Task 11 docs/config surface for Telegram Business dialog profiles.
- Target: Existing website Telegram docs; task package execution ledger.
- Boundaries: Documentation only; no runtime code changes; container-only docs-related checks only; no host npm/pytest/uv.
- Done when: Docs cover DB-backed settings, dashboard and bot editing, three participant prompt model, command safety, prefix, modes, and `invocation_policy`; coherent commit created.

## Context
- Slice: Task 11 documentation/config surface.
- Task package: `docs/plans/2026-06-09-telegram-business-dialog-profiles`.
- Worktree: `/tmp/pi-worktree-68b05a6c-1`.
- Branch: `pi-parallel-68b05a6c-1`.
- Commit: `c57bbc33d docs: document Telegram Business dialog profiles`.

## Spec compliance
- DB-backed settings source of truth: done in `website/docs/user-guide/messaging/telegram.md`.
- Dashboard settings UI editing path: done; documents settings card and `GET`/`PATCH /api/business/chats/{token}/settings`.
- Telegram bot Prompt/Clear buttons: done; documents `/business`, **🧠 Prompt**, and **🧹 Clear prompt** semantics.
- Three participant prompt model: done; documents owner/operator, customer/contact, and Hermes assistant.
- Command safety: done; documents customer slash-like messages are not operator commands and owner manual outgoing messages are context.
- Prefix, modes, `invocation_policy`: done; documents `🤖 Hermes:` default prefix, watch/draft/auto modes, and `off`/`mention_draft`/`mention_direct`.

## Acceptance verification
- Static docs acceptance read:
  - Result: passed.
  - Evidence: `grep -n "DB-backed\|source of truth\|Prompt\|Clear prompt\|invocation_policy\|Customer text\|manual outgoing" website/docs/user-guide/messaging/telegram.md` found all required topics.
- Container-only docs build:
  - Result: not completed due environment gap.
  - Evidence: `docker run --rm -v "$PWD":/workspace -w /workspace/website hermes-agent:test-runner-assets npm run build` failed with `sh: 1: docusaurus: not found`; no host package/test commands were run.

## Changed files
- `website/docs/user-guide/messaging/telegram.md`
- `docs/plans/2026-06-09-telegram-business-dialog-profiles/plan.md`
- Progress updated at `/home/kcnc/code/hermes/hermes-agent/.worktrees/telegram-business-dialog-profiles/progress.md`.

## Issues
- R-01: Existing Telegram Business docs described the old text-only MVP and edit-out-of-scope language. Resolved by replacing it with current dialog profile/settings behavior and explicit Prompt/Clear controls.
- U-01: Full Docusaurus build could not run in the available container image because Docusaurus dependencies are absent. This is a verification environment limitation, not a docs content blocker.

## Verdict
Task 11 docs/config surface is complete and committed. System readiness for this docs-only slice is acceptable with static evidence; full website build remains unverified pending a container image with website dependencies.
