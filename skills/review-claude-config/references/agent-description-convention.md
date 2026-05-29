---
name: agent-description-convention
description: Authoring rules for agent-frontmatter `description:` field — cluster-density-aware length, Quality-First hierarchy, reciprocal counter-case symmetry, lead-with-Use-this-when phrasing.
last_refreshed: 2026-05-07
---

# Agent Description Convention

Authoring rules for the `description:` field in agent frontmatter.
Evidence class follows `description-design-problem.md` — P/E/L/R notation.

## 1. Lead-with "Use this when X" `[E]`

The first sentence of any agent description MUST start with `Use this when …` or
`Use to …`. This is the Anthropic skill-creator convention for routing precision.

- **PASS:** "Use this when reviewing PR diffs for security regressions."
- **FAIL:** "Reviews code." (no trigger phrase; generic noun-verb snippet)

## 2. Cluster-Density-Aware Length `[E]`

No *platform* character cap applies below Anthropic's 1024-char absolute ceiling.
Separately, the team applies a ≤250-char conciseness standard: a review flagging a
description >250 chars cites that team standard (`Repo default`, Medium), NOT a
platform error — 251–1024 chars are platform-valid but above team standard.
Length otherwise scales with the number of competing primitives in the same trigger
cluster — more competition needs more disambiguation tokens. A single-agent repo
may succeed with 40 chars; a 10-agent plugin requires 150–300 chars to route
reliably.

Reference: Microsoft 775-tool catalog — collision probability rises sharply when
descriptions share ≥2 trigger tokens across ≥5 siblings.

## 3. Quality-First / Token-Tiebreaker Hierarchy `[E]`

Quality (DQ-1..3 Purpose/Guidelines/Limitations) is the **primary axis**.
Token economy is the tiebreaker only when two phrasings have equal DQ-coverage.

Empirical rationale: Saavedra arXiv 2602.14878 — 97.1% of MCP descriptions exhibit
≥1 smell. Quality gaps dominate; length optimization is secondary.

## 4. Counter-Case Reciprocal Symmetry `[E]`

If primitive A's description says "do NOT use; use B", primitive B's description
MUST contain a corresponding negative entry naming A.

Example triangle: `review-skill` ↔ `review-agent` ↔ `review-rule`. Each carries
"Do NOT use for [other-primitive] files — use [sibling] instead."

Asymmetric counter-cases create silent over-triggering when A is absent from B's
scope exclusions.

## 5. Concrete-User-Phrase Preference `[E]`

Prefer the verbatim phrasing a user types ("review this agent", "audit my repo")
over abstract task-types ("conduct quality assessment", "perform evaluation").

- **PASS:** "Use when asked to 'review agent' or dispatched by /review-claude-config."
- **FAIL:** "Performs comprehensive multi-dimensional quality assessment of agent primitives."

## 6. Empirical Anchor Cross-Reference

**Empirical anchor:** see [`description-design-problem.md`](description-design-problem.md) — do not duplicate the empirical numbers here.
