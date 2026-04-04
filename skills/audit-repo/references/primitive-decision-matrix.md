---
name: primitive-decision-matrix
description: Evidence-informed decision aids for recommending each Claude Code primitive type
last_refreshed: 2026-04-03
---

## CLAUDE.md (P0) `[Engineering guidance + Repo default]`

Recommend when: information is universally needed every session.
- Toolchain commands (build, test, lint, deploy)
- Architecture overview + entry points (ambiguous paths only)
- Scope boundaries, domain doc pointers, large file hints (>500 LOC)

Budget: <200 lines. Progressive disclosure — point to docs, don't inline.

## Hook (P1) `[Engineering guidance + Repo default]`

Recommend when: constraint is mechanical and verifiable after tool use.
- Convention linter with no auto-fix → PostToolUse formatter
- Secret patterns → PreToolUse check before write
- Single boolean command → Hook. Judgment needed → Rule or CLAUDE.md.

## Skill (P1) `[Repo default]`

Recommend when: workflow is repeated, multi-step, parameterizable.
- ≥5 similar files + identifiable skeleton, multi-stage CI, or codegen templates

Must pass 3/4: recurrence, verification, non-obviousness, generalizability.

## Agent (P2) `[Repo default — conservative]`

Recommend when: concern has BOTH its own toolchain AND evaluation criteria.
- Separate configs per subdomain, security scanning, separate deploy targets
- Own files but same toolchain → Skill, not Agent.

## Instruction Budget `[Engineering guidance + Repo default]`

IFScale: 100-250 simple instructions before cliff decay; Claude Code uses ~50. Effective budget: ~100-150 across all primitives. Keep CLAUDE.md lean — remove instructions Claude already follows.
