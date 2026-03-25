---
name: rule-evaluation-guide
description: Type-specific evaluation criteria for Claude Code rules (plain .md files in rules/ directory)
---

# Rule Evaluation Guide

Rules are always-active constraints applied to all conversations. They have no tools, no standardized frontmatter, and are directives — not workflows. Only 3 dimensions apply.

## Clarity Assessment (30%)
- Could two different models interpret this rule differently?
- Are terms precisely defined (not "appropriate", "good", "reasonable")?
- Is scope explicit (which files, which operations, which contexts)?
- Are action verbs unambiguous ("must", "never" vs "should", "try to")?

## Completeness Assessment (30%)
- Are edge cases addressed?
- Are exceptions explicitly stated (when does the rule NOT apply)?
- Are scope boundaries defined?
- Does the rule interact with other rules? Are conflicts addressed?
- For rules referencing external tools/commands: are version or format assumptions explicit?

## Goal Alignment Assessment (40%)
- Does the rule achieve its stated constraint?
- Is the constraint proportional (not overly broad or narrow)?
- Would the rule prevent the specific behavior it targets?
- Are there obvious workarounds the rule doesn't address?
- Does domain knowledge reveal missing constraints?

## Why Only 3 Dimensions
Rules lack tools (→ Safety irrelevant), frontmatter (→ Metadata irrelevant), and are directives not prompts (→ PE, CE irrelevant). This is structural, not a quality judgment.

## Common Rule Anti-Patterns
- Vague directives ("write good code") without measurable criteria
- Rules that conflict with tool capabilities or other rules
- Overly broad scope (applies to everything, enforces nothing specific)
- No scope boundaries (no indication of when the rule doesn't apply)
- Aspirational language ("try to", "when possible") instead of constraints
