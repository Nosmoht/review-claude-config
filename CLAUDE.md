# Review Claude Config

A Claude Code skill that analyzes and optimizes Claude Code skills and agents using evidence-based prompt and context engineering evaluation.

## Skills

- `/review-claude-config [folder]` — Audit all skills/agents in a folder (defaults to cwd). Read-only, produces per-item quality certificates.
- `/refresh-engineering-baseline` — Update the engineering baseline with current research via WebSearch.

## Installation

Copy both skill directories into any project's `.claude/skills/`:
```
cp -r .claude/skills/review-claude-config <target>/.claude/skills/
cp -r .claude/skills/refresh-engineering-baseline <target>/.claude/skills/
```

## File Structure

- `.claude/skills/review-claude-config/SKILL.md` — Main orchestrator skill
- `.claude/skills/review-claude-config/references/scoring-rubric.md` — 7-dimension A-F grading rubric
- `.claude/skills/review-claude-config/references/engineering-baseline.md` — Curated prompt, context, and tool design techniques
- `.claude/skills/refresh-engineering-baseline/SKILL.md` — Baseline refresh skill

## Conventions

- Language: English
- Reference files must stay within token budgets: rubric <1K, baseline <2K
- The review skill is read-only — it never modifies analyzed files
- The baseline is static at review time; updates happen via `/refresh-engineering-baseline`

## Working Guidelines

- **Verify subagent claims with evidence.** When a subagent/reviewer recommends changing the approach, verify the underlying assumptions with WebSearch or other evidence before accepting. Do not remove features without proof they don't add value. (Context: a reviewer once recommended dropping domain-specific research — we verified and found the reviewer was wrong, domain knowledge improves quality by 30-206%.)
- **Iterate reviews until convergence.** After each review round, address findings, then launch another review. Stop only when a review returns no high/medium priority findings. Don't accept the first review as final.
- **Every claim needs a source.** All research files, documentation, and recommendations must link to verifiable sources. Follow the [documentation best practices](research/documentation/engineering-documentation-best-practices.md) used in this project.
