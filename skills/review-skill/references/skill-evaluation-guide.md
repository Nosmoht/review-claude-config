---
name: skill-evaluation-guide
description: Type-specific evaluation criteria for Claude Code skills (SKILL.md files)
last_refreshed: 2026-04-03
---

# Skill Evaluation Guide

## Progressive Disclosure
- Is stable knowledge in `references/` files, not inline?
- Is main SKILL.md under 500 lines?
- Are supplementary files loaded on-demand (Read) rather than pre-loaded?
- Does the skill use subagent isolation for complex subtasks?
- Are activation boundaries clear without matching unrelated requests?

## Workflow Structure
- Are steps numbered with explicit sequential dependencies?
- Are conditional branches defined with measurable criteria (not "if needed")?
- Are parallel vs sequential steps explicitly marked?
- Are stop conditions and recovery actions defined?

## Reference File Quality
- Does each reference file stay within token budgets? (See `check-repo-health` thresholds.)
- Is each reference single-purpose?
- Could any reference content be eliminated without losing capability?

## Argument Handling
- Is `$ARGUMENTS` parsed with validation?
- Are defaults specified for missing arguments?
- Is error handling for invalid arguments present?
- Does `argument-hint` accurately describe the expected input?

## Output Format
- Is the output format specified with a literal template or example?
- Are all sections/fields defined?
- Does the output format prevent downstream context bloat?
- For review skills: do findings include `Evidence:` and `Validation:`?

## Safety Patterns (for skills with Write/Bash/Edit)
- Confirmation gates before destructive or irreversible operations?
- Least-privilege tool set (`allowed-tools` matches actual usage)?
- Stop conditions defined for loops or recursive operations?

## Common Skill Anti-Patterns
- Inline embedding of content that belongs in reference files
- Tool list includes tools never referenced in the workflow
- Missing output format specification (relying on implicit model behavior)
- No error handling for tool failures or unavailable tools
