# Change Discipline Rule
**Portable — copy to `.claude/rules/change-discipline.md` in any project.**

## Rule: Zero Medium findings before commit

Every change follows this mandatory sequence. No step may be skipped.

1. **Plan** — design the change; have it reviewed by a subagent before proceeding
2. **Review** — launch one or more review subagents against the planned change; address all High and Medium findings
3. **Implement** — make the change
4. **Review** — launch review subagents against the implemented change; address all High and Medium findings; re-review until clean
5. **Commit** — only when the final review reports no High or Medium findings

Low findings must be reported and recorded, but do not block the commit.

## Non-negotiables

- A commit with any unresolved High or Medium finding is a process violation.
- "I'll fix it in the next commit" is not acceptable for High or Medium findings.
- Carry-forward Mediums from a prior round must be explicitly documented as accepted risk with rationale — they do not disappear.
- Re-reviews after fixes must be full re-reviews, not spot-checks on the changed lines only.

## Why

Medium findings cause real failures: dual-write races, MCP tool gaps, broken dependency chains, ambiguous authority between rules. In this session, every Medium that slipped through commit required a follow-up fix commit. The overhead of re-review is lower than the overhead of debugging silent failures in autonomous execution.
