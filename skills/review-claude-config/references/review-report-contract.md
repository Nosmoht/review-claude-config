---
name: review-report-contract
description: Canonical review certificate, recommendation, and report frontmatter contract for review producers and consumers
---

# Review Report Contract

This file is the only normative source for the forward-looking review/report contract used by:

- `review-claude-config`
- `review-skill`
- `review-agent`
- `review-rule`
- `apply-review-findings`
- `apply-skill-review-findings`
- `apply-agent-review-findings`
- `apply-rule-review-findings`
- `review-analytics`
- `check-repo-health`

Keep producer-specific behavior, category vocabularies, menus, type-specific validation, and legacy-consumer tolerance in the individual skills. Keep only report structure, recommendation structure, and identity rules for newly written reports here.

## Certificate Shape

Every review certificate uses the same top-level section order:

1. `Goal`
2. `Certificate`
3. `Strengths`
4. `Recommendations`

Reviewers may insert review-specific calibration or batch-only sections between `Certificate` and `Strengths` when needed. This does not change the canonical base shape.

## Recommendation Block

Every recommendation heading uses this format:

```markdown
#### N. [Title] (Impact: [High/Medium/Low][, Category: ...])
```

Required fields:

- `Evidence`
- `Why it matters`
- `Validation`

Optional fields:

- `Current`
- `Recommended`

Canonical structure:

~~~markdown
#### 1. [Title] (Impact: [High/Medium/Low], Category: [...])
**Evidence:** [quoted text, path, or section reference]

**Why it matters:** [short explanation]

**Validation:** [how to confirm on re-review]

**Current:**
~~~text
[existing text]
~~~

**Recommended:**
~~~text
[replacement text]
~~~
~~~

`Current` and `Recommended` are optional in review output. Mutation-oriented apply consumers may require both fields before they can safely dispatch an edit. Legacy parsing tolerance is defined by each consumer, not by this contract.

**Terminology note:** This repo uses "dispatchable" for recommendations that include both `Current` and `Recommended` rewrite anchors, and "manual-only" for valid findings that lack rewrite anchors. "Dispatchable" is equivalent to "auto-fixable" or "fixable" in ESLint (`meta.fixable`), LSP (`CodeActionKind.QuickFix`), SonarQube, and Roslyn (`CodeFixProvider`).

## Report Frontmatter

All review report producers use the same frontmatter contract:

```yaml
---
generated_by: review-skill|review-agent|review-rule|review-claude-config
schema_version: 1
date: YYYY-MM-DD
target: /absolute/path
baseline_version: YYYY-MM-DD
items_reviewed: N
summary:
  - name: item-name
    type: Skill|Agent|Rule
    path: relative/path/to/file
    overall: B
    score: 85.0
    clarity: B
    completeness: A
    prompt_engineering: B
    context_engineering: B
    goal_alignment: B
    safety: A
    metadata: B
---
```

Rules keep non-applicable dimensions as `null`:

- `prompt_engineering: null`
- `context_engineering: null`
- `safety: null`
- `metadata: null`

## Identity and Tracking

- `type + path` is the canonical identity across reports.
- `name` is display-only and must not be used as the primary analytics key.
- If a path disappears and a new path appears, treat it as a rename/move candidate rather than silently merging by name.

## Producer Compatibility

- Single-item reports and batch reports use the same recommendation schema and the same frontmatter summary schema for newly generated reports.
- `generated_by` stays producer-specific.
- `schema_version` remains `1` unless a real breaking producer change is introduced.
- Historical report tolerance is consumer-specific and must not be inferred from this file.

## Dimensions

Full review reports use these summary fields:

- `clarity`
- `completeness`
- `prompt_engineering`
- `context_engineering`
- `goal_alignment`
- `safety`
- `metadata`

Rules use the same summary field names but keep the non-applicable ones as `null`.
