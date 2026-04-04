---
name: skill-fix-guide
description: Type-specific validation rules for applying fixes to Claude Code skills
last_refreshed: 2026-03-25
---

# Skill Fix Guide

## Line Count

SKILL.md must stay under 500 lines. If an edit would exceed this, suggest extracting stable content to `references/` as a manual follow-up.

## Reference File Token Budget

Each file in `references/` must be under 500 tokens (~385 words). Estimate with word count x 1.3. Warn if a reference file edit exceeds this.

## Progressive Disclosure

Stable knowledge (lookup tables, static templates, long examples) belongs in `references/`, not inline in SKILL.md. If an edit inlines such content, flag it as a manual follow-up for extraction. The applier is edit-only and must not create new files.

## Frontmatter Validation

After edits, verify:
- `name` and `description` are present and non-empty
- `allowed-tools` matches tools actually referenced in the workflow body
- `argument-hint` is present if the skill accepts arguments
- `disable-model-invocation: true` is set if the skill uses Write/Edit/Bash for side effects

## Workflow Structure

Numbered steps must remain sequentially coherent after edits. Conditional branches ("if X then Y") must have measurable criteria -- not vague qualifiers like "if needed" or "when appropriate."

## Common Pitfalls

- Don't break existing `references/` file Read paths when renaming sections
- Don't add tools to `allowed-tools` that aren't used in the workflow
- Don't remove stop conditions or error handling
- Don't merge separate phases into one (preserves user confirmation boundaries)
