# Acceptance plan — upstream sync/merge 2026-06-09

Audit focus: compare `plan.md` AC1–AC6 against `final-report.md`, `verification/final.md`, and slice reports.

## Evidence sources
- `final-report.md`
- `verification/final.md`
- `reports/slice-gateway-telegram.md`
- `reports/slice-agent-providers-tools.md`
- `verification/gateway-telegram.md`
- `verification/agent-providers-tools.md`

## Criteria to check
- AC1: upstream merged into local fork branch
- AC2: accidental empty checkpoint dropped
- AC3: local fork behavior preserved/adapted
- AC4: conflicts resolved cleanly
- AC5: container-only verification with exact commands/results
- AC6: final report completeness (files/commits/verification/risks/continuation)

## Audit approach
- Confirm each AC has direct evidence, not just related commentary.
- Separate file-state evidence from runtime/test evidence.
- Mark container-only verification as failed only if any host-side test/build/install evidence is used.
- Treat blocked container tests/builds as acceptable only if the blocker is explicit, current, and scoped.
