---
name: primitive-decision-matrix
description: Decision rules for recommending each Claude Code primitive type
---

## CLAUDE.md (P0)

Recommend when: information is universally needed every session.
- Toolchain commands (build, test, lint, deploy)
- Architecture overview + entry points (only for ambiguous paths)
- Scope boundaries (monorepo package isolation)
- Domain doc references (pointers, not inline content)
- Large file hints (>500 LOC: "relevant logic in lines X-Y")

Budget: <200 lines. Use progressive disclosure — point to docs, don't inline.

## Hook (P1)

Recommend when: constraint is mechanical and verifiable after tool use.
- Convention has linter but no auto-fix → PostToolUse runs formatter
- Secret patterns in code → PreToolUse checks before write
- Branch protection → simpler as a Rule ("Never commit to main")

Decision: single command with boolean output → Hook. Judgment needed → Rule or CLAUDE.md.

## Skill (P1)

Recommend when: workflow is repeated, multi-step, parameterizable.
- ≥5 structurally similar files + identifiable skeleton → scaffolding skill
- Multi-stage CI workflow reproducible locally → workflow skill
- Existing codegen templates (plop, hygen) → wrapper skill

Must pass 3/4 extraction criteria: recurrence, verification, non-obviousness, generalizability.

## Agent (P2)

Recommend when: concern has BOTH its own toolchain AND own evaluation criteria.
- Separate lint/test configs per subdomain → specialized review agent
- Security scanning in CI → security-reviewer agent
- Separate deployment targets → infra-architect agent

Decision: own files but same toolchain → Skill, not Agent.

## Instruction Budget

IFScale benchmark: reasoning models handle 100-250 simple instructions before cliff decay. Claude Code system prompt uses ~50. Effective budget: ~100-150 across all primitives. Keep CLAUDE.md lean — remove instructions Claude already follows without being told.
