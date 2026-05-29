---
name: skill-description-convention
description: Authoring rules for skill-frontmatter `description:` field — cluster-density-aware length, Quality-First hierarchy, reciprocal counter-case symmetry, lead-with-Use-this-when phrasing.
last_refreshed: 2026-05-07
---

# Skill Description Convention

Authoring rules for the `description:` field in skill frontmatter.
Evidence class follows `description-design-problem.md` — P/E/L/R notation.

## 1. Lead-with "Use this when X" `[E]`

The first sentence of any skill description MUST start with `Use this when …` or
`Use to …`. This is the Anthropic skill-creator convention for routing precision.

- **PASS:** "Use this when reviewing a SKILL.md for quality issues."
- **FAIL:** "Reviews skills." (no trigger phrase; generic noun-verb snippet)

## 2. Cluster-Density-Aware Length `[E]`

No *platform* character cap applies below Anthropic's 1024-char absolute ceiling.
Separately, the team applies a ≤250-char conciseness standard: a review flagging a
description >250 chars cites that team standard (`Repo default`, Medium), NOT a
platform error — 251–1024 chars are platform-valid but above team standard.
Length otherwise scales with the number of competing skills in the same plugin —
more siblings in the same trigger cluster requires more disambiguation tokens.

Reference: Microsoft 775-tool catalog — collision probability rises sharply when
descriptions share ≥2 trigger tokens across ≥5 siblings in the same plugin.

## 3. Quality-First / Token-Tiebreaker Hierarchy `[E]`

Quality (DQ-1..3 Purpose/Guidelines/Limitations) is the **primary axis**.
Token economy is the tiebreaker only when two phrasings have equal DQ-coverage.

Empirical rationale: Saavedra arXiv 2602.14878 — 97.1% of MCP descriptions exhibit
≥1 smell. Quality gaps dominate; length optimization is secondary.

## 4. Counter-Case Reciprocal Symmetry `[E]`

If skill A's description says "do NOT use; use B", skill B's description MUST
contain a corresponding negative entry naming A.

Example pair: `review-skill` ↔ `review-agent`. Each description carries an
explicit "not for [other primitive]" clause pointing to the sibling.

Asymmetric counter-cases create silent over-triggering when A is absent from B's
scope exclusions.

## 5. Concrete-User-Phrase Preference `[E]`

Prefer the verbatim phrasing a user types ("review this skill", "check my hook")
over abstract task-types ("evaluate quality of skill artifact").

- **PASS:** "Use when asked to 'review skill' or dispatched by /review-claude-config."
- **FAIL:** "Performs comprehensive multi-dimensional quality evaluation of skill primitives."

## 6. Skill-Specific Activation Note

Skill body is loaded **only on activation**; SKILL.md ≤ 5,000 tokens (Anthropic
Agent Skills Specification, April 2026). The `description:` field is the routing
surface and the **only level-1 token cost** — every byte not needed for routing
is overhead in every dispatch, not just the first.

## 7. Empirical Anchor Cross-Reference

**Empirical anchor:** see [`description-design-problem.md`](description-design-problem.md) — do not duplicate the empirical numbers here.
