---
name: rule-evaluation-guide
description: Type-specific evaluation criteria for Claude Code rules (plain .md files in rules/ directory)
last_refreshed: 2026-04-03
---

# Rule Evaluation Guide

Rules are always-active constraints with no tools, frontmatter, or prompt structure — so PE, CE, Safety, and Metadata are structurally inapplicable. Only Clarity (30%), Completeness (30%), and Goal Alignment (40%) apply.

## Clarity Assessment (30%)
- Could two different models interpret this rule differently?
- Are terms precisely defined (not "appropriate", "good", "reasonable")?
- Is scope explicit (which files, which operations, which contexts)?
- Are action verbs unambiguous ("must", "never" vs "should", "try to")?
- Can a reviewer point to concrete text as evidence for each claimed problem?

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

## Common Rule Anti-Patterns
- Vague directives ("write good code") without measurable criteria
- Rules that conflict with tool capabilities or other rules
- Overly broad scope (applies to everything, enforces nothing specific)
- No scope boundaries (no indication of when the rule doesn't apply)
- Aspirational language ("try to", "when possible") instead of constraints
- Recommendations that cannot be re-checked on a follow-up review
