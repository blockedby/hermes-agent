# My changes in blockedby's Hermes Agent fork

Hermes Agent is an upstream open-source project by NousResearch and the Hermes Agent maintainers.
This file does not claim original authorship of Hermes Agent.
It summarizes selected engineering work in Alexander Longov's (`blockedby`) public fork:
<https://github.com/blockedby/hermes-agent>.

The focus of this fork work is Telegram Business gateway behavior, messaging/session reliability,
and public verification evidence for the fork.

## Commit evidence

Comparison basis: local fork branch changes that are not in upstream `origin/main`, inspected with `git log --oneline --no-merges origin/main..HEAD` and selected `git show --name-only` evidence.
Commit links below point to the public fork.

| Commit | Area | Evidence summary |
| --- | --- | --- |
| [`c34755af6`](https://github.com/blockedby/hermes-agent/commit/c34755af6) | Setup/config reliability | Kept local speech-to-text endpoint compatibility in `tools/transcription_tools.py` with regression coverage in `tests/tools/test_transcription_tools.py`. |
| [`eaa54d30a`](https://github.com/blockedby/hermes-agent/commit/eaa54d30a) | Telegram Business approvals | Added Telegram Business approval drafts across `gateway/platforms/base.py`, `gateway/platforms/telegram.py`, `gateway/run.py`, tests, and Telegram user docs. |
| [`e3761b0e7`](https://github.com/blockedby/hermes-agent/commit/e3761b0e7) | Telegram Business message safety | Ignored Telegram Business self messages in `gateway/platforms/telegram.py`, with tests and docs updates. |
| [`e16c598a3`](https://github.com/blockedby/hermes-agent/commit/e16c598a3) | Messaging/session behavior | Handled Telegram DM topics safely across Telegram gateway routing, image/document sending tests, approval-button tests, and thread fallback tests. |
| [`bdce783e9`](https://github.com/blockedby/hermes-agent/commit/bdce783e9) | Session isolation tests | Added `tests/gateway/test_telegram_session_isolation.py` coverage for Telegram session-key isolation. |
| [`c79185730`](https://github.com/blockedby/hermes-agent/commit/c79185730) | Topic/thread tests | Added Telegram Business topic/thread helper coverage in `tests/gateway/test_telegram_business.py` and `tests/gateway/test_telegram_thread_fallback.py`. |
| [`7894d14a3`](https://github.com/blockedby/hermes-agent/commit/7894d14a3) | Approval context | Stored Telegram Business approval context in the Telegram adapter with regression tests. |
| [`28c2c1f6c`](https://github.com/blockedby/hermes-agent/commit/28c2c1f6c) | Approval audit hardening | Hardened Telegram Business approval audit behavior in `gateway/platforms/telegram.py`, `gateway/platforms/telegram_business_approvals.py`, `gateway/session.py`, tests, and docs. |
| [`28606f1d0`](https://github.com/blockedby/hermes-agent/commit/28606f1d0) | Per-chat modes | Added Telegram Business per-chat modes in `gateway/platforms/telegram.py`, `gateway/platforms/telegram_business_chats.py`, `gateway/run.py`, slash-command registration, docs, and tests. |
| [`0446b4e5c`](https://github.com/blockedby/hermes-agent/commit/0446b4e5c) | Session fallback routing | Preserved business session-key fallback routing in `gateway/run.py` with `tests/gateway/test_session_key_parse_fallback.py`. |
| [`51a71d122`](https://github.com/blockedby/hermes-agent/commit/51a71d122) | Business mode actions | Triggered Telegram Business mode actions immediately in the Telegram adapter and business chat helper with tests. |
| [`4bfb9c75e`](https://github.com/blockedby/hermes-agent/commit/4bfb9c75e) | Owner draft framing | Framed Telegram Business replies as owner drafts in `gateway/session.py` with session tests. |
| [`66c9ea6fc`](https://github.com/blockedby/hermes-agent/commit/66c9ea6fc) | Runtime state | Initialized Telegram Business runtime state in `gateway/platforms/telegram.py`. |
| [`49baf28c6`](https://github.com/blockedby/hermes-agent/commit/49baf28c6) | DM topic regression | Kept Telegram Business thread markers out of DM topics in `gateway/platforms/telegram.py`, `gateway/run.py`, and regression tests. |
| [`6ffa1b983`](https://github.com/blockedby/hermes-agent/commit/6ffa1b983) | Dashboard scaffold | Scaffolded the Telegram Business dashboard app under `apps/telegram-business-dashboard/`. |
| [`4e7582668`](https://github.com/blockedby/hermes-agent/commit/4e7582668) | Dashboard auth tests | Added Telegram dashboard auth tests and fixtures for session/API authentication. |
| [`3228303c2`](https://github.com/blockedby/hermes-agent/commit/3228303c2) | Dashboard API | Added Telegram Business dashboard API support in `gateway/platforms/telegram_business_dashboard_api.py` with gateway tests. |
| [`f3be21ea1`](https://github.com/blockedby/hermes-agent/commit/f3be21ea1) | Dashboard history | Recorded Telegram Business dashboard history via Telegram adapter/history/API helpers with tests. |
| [`5418f2cb2`](https://github.com/blockedby/hermes-agent/commit/5418f2cb2) | Dashboard BFF routes | Added Next.js API routes for Telegram Business chats, drafts, history, and modes. |
| [`d0808d9d2`](https://github.com/blockedby/hermes-agent/commit/d0808d9d2) | Dashboard UI | Added Telegram Business dashboard UI components, client API helpers, view-model code, and Vitest coverage. |
| [`3a341c5e8`](https://github.com/blockedby/hermes-agent/commit/3a341c5e8) | Dashboard launch/config | Added Telegram Business dashboard launcher wiring through `gateway/config.py`, `gateway/platforms/telegram.py`, `hermes_cli/config.py`, and config tests. |
| [`954d4f60a`](https://github.com/blockedby/hermes-agent/commit/954d4f60a) | Dashboard API hardening | Hardened Telegram Business dashboard API and BFF request handling with gateway and route-handler tests. |
| [`52d93fa27`](https://github.com/blockedby/hermes-agent/commit/52d93fa27) | Telegram launch data | Captured Telegram launch init data in dashboard launch-param helpers and tests. |
| [`7b5db852a`](https://github.com/blockedby/hermes-agent/commit/7b5db852a) | Telegram Business media | Ingested Telegram Business media across Telegram adapter, history, gateway routing, STT config tests, and business tests. |
| [`8da24bb2e`](https://github.com/blockedby/hermes-agent/commit/8da24bb2e) | Dashboard API embedding | Embedded Telegram Business dashboard API into the Telegram adapter. |
| [`ea07cd470`](https://github.com/blockedby/hermes-agent/commit/ea07cd470) | Dashboard drafts | Kept business draft generation available in dashboard API/routes/components/history code with tests and task-package verification. |
| [`3011c9568`](https://github.com/blockedby/hermes-agent/commit/3011c9568) | Dashboard session lease | Added Telegram dashboard session lease behavior across session route, business routes, server auth helper, and tests. |

## Touched areas summary

- `gateway/platforms/telegram.py`: Telegram Business message routing, approval draft behavior, mode actions, self-message filtering, media ingestion, dashboard API integration, and session/topic safeguards.
- `gateway/run.py` and `gateway/session.py`: Telegram Business session fallback routing, approval/control flow context, and owner-draft framing.
- `gateway/platforms/telegram_business_*.py`: helper modules for approvals, business chats, dashboard API, and message history.
- `apps/telegram-business-dashboard/`: Next.js dashboard scaffold, Telegram auth/session route, business BFF routes, UI components, client API helpers, and Vitest tests.
- `hermes_cli/config.py`, `gateway/config.py`, and `hermes_cli/commands.py`: configuration and command wiring for Telegram Business dashboard/mode features.
- `tests/gateway/`, `tests/hermes_cli/`, and dashboard tests: regression coverage for Telegram Business behavior, session isolation, topic fallback, dashboard API/auth/UI, config, STT compatibility, and media handling.
- `website/docs/user-guide/messaging/telegram.md` and `docs/telegram-business-modes.md`: public documentation for Telegram Business workflows.

## Verification notes

This attribution file is based on repository evidence, not private runtime logs. Useful local evidence commands:

```bash
git log --oneline --no-merges origin/main..HEAD
git diff --stat origin/main...HEAD -- gateway/platforms/telegram.py gateway/run.py gateway/session.py hermes_cli/config.py tests/gateway tests/hermes_cli apps/telegram-business-dashboard docs/telegram-business-modes.md website/docs/user-guide/messaging/telegram.md
git show --name-only --format='%h %s' <commit>
```

Narrow docs-safe verification for this file should include:

```bash
git diff --check
# Run the repo's public-doc safety scan for secrets, private URLs, forbidden phrases, and upstream ownership overclaims.
git status --short --branch
```

No live Telegram bot credentials, chat identifiers, webhook URLs, private endpoints, raw logs, or real user data are intentionally included here.
