---
name: skill-fix-guide
description: Type-specific validation rules for applying fixes to Claude Code skills
last_refreshed: 2026-05-13
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

## Decorative-to-Functional Role-Statement Rewrite

Per [`skill-agent-format-conventions.md` §Role Statements](../../../research/claude-code/skill-agent-format-conventions.md), role statements must use functional form (`You are a <noun-phrase> that <verb-phrase>`) — no decorative adjectives. Evidence: arXiv:2602.12285, arXiv:2603.18507.

**Detection** — scan body opening lines for an adjective between `You are a/an` and the role-noun (e.g., `strict`, `disciplined`, `expert`, `experienced`, `senior`, `world-class`, `meticulous`, `rigorous`). The list is non-exhaustive; flag any adjective that decorates the role-noun without naming a verifiable behavior.

**Out-of-scope** — do NOT rewrite role statements inside (a) fenced code blocks, (b) lines explicitly marked as `before` / `anti-pattern` / `example` examples, or (c) quoted content within a `> ` blockquote. The pattern's own before/after example is teaching content, not a violation.

**Before** → **After** (illustrative):

- `You are a strict but fair evaluator that verifies ACs.`
- → `You are an evaluator that verifies ACs.` + new constraint *(intent-preserving translation needed — see step 2)*

**4-step rewrite**:

1. Extract decorative adjective(s) prepending the role-noun; keep the functional noun.
2. Translate each adjective to a behavioral constraint **only after reading the agent's existing constraints to preserve calibration polarity**. The same adjective can map to opposing constraints depending on context:
   - `strict`: examine whether the agent currently optimizes for low-FP-rate (precision) or low-FN-rate (recall). Translate accordingly. Do not assume.
   - `disciplined`: scope discipline (no scope-expansion) vs. process discipline (follow phases) — pick based on the agent's existing workflow section.
   - `experienced` / `expert` / `senior` / `world-class`: prefer DELETE; only translate if downstream prompts demonstrably depend on the seniority signal (e.g., verbosity, hedging style). Document any non-DELETE choice in the commit body.
3. Append translated constraints to the existing constraints section. Do NOT contradict an existing constraint — if the translation would contradict, flag as manual review.
4. Verify: body-opening role statement matches `You are an? <noun-phrase> that <verb-phrase>`; no decorative adjectives remain in the role-noun phrase. Multi-word phrases (`strict but fair`, `experienced senior`) must be fully resolved, not just the first adjective.

Limitations: this pattern detects body-opening role statements only. Non-opening role statements (body line ≥10) and definite-article forms (`You are the strict X`) require manual review. The applier is edit-only — if a rewrite needs a new reference file, flag as manual follow-up.
