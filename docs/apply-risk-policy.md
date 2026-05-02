---
name: apply-risk-policy
description: Declarative pre-apply decision matrix for apply-* skills on evidence_class × confidence × blast_radius → auto_apply_allowed
last_refreshed: 2026-05-02
---

# Apply-Risk Policy

Declarative classification layer consumed by all apply-* skills before
any file mutation. The policy decides whether to ENTER an Edit; the
per-edit Confirmation Gate (already in each apply-* SKILL.md
`## Hard Rules`) still runs on every Edit — the two layers compose,
the Gate is not replaced.

## Schema

Field shapes used by `decide()` and the matrix below:

- `evidence_class`: enum `[Proven result, Engineering guidance, Repo default, Low-evidence area]`
  (mirrors `skills/review-claude-config/references/evidence-contract.md`)
- `confidence`: enum `[high, medium, low]`
- `blast_radius`: enum `[single-file, multi-file, runtime-behavior, security-sensitive]`
- `change_type`: enum `[formatting, structure, wording, policy, tool-permission, hook, apply-flow]`
  (taxonomic only — does not participate in `decide()`)
- `auto_apply_allowed`: bool — whether the skill may proceed without additional
  manual-only routing
- `human_review_required`: bool — whether the change must be routed to manual
  human review before applying

## Decision Matrix

Baseline outcomes for 4 `evidence_class` values × 3 `confidence` levels.
Override rules (§Override Rules) are evaluated BEFORE the matrix and
short-circuit it; the matrix is reached only when no override fires.

| evidence_class | confidence | auto_apply_allowed | human_review_required |
|---|---|---|---|
| Proven result | high | true | false |
| Proven result | medium | false | true |
| Proven result | low | false | true |
| Engineering guidance | high | true | false |
| Engineering guidance | medium | false | true |
| Engineering guidance | low | false | true |
| Repo default | high | true | false |
| Repo default | medium | false | true |
| Repo default | low | false | true |
| Low-evidence area | high | false | true |
| Low-evidence area | medium | false | true |
| Low-evidence area | low | false | true |

## Override Rules

Override rules are evaluated BEFORE matrix lookup (short-circuit
semantics). Priority order: O3 → O1 → O2 → matrix baseline. Once any
override fires, no further rules are evaluated.

- **O3 (Hard rule, Boundaries §Never)**: `evidence_class == null`
  (missing label) ⇒ `auto_apply_allowed: false, human_review_required: true`.
  Never auto-apply findings without an `evidence_class` label.
- **O1 (Hard rule, Boundaries §Always)**: `evidence_class == "Low-evidence area"`
  ⇒ `auto_apply_allowed: false, human_review_required: true`. Redundant
  by design with the matrix bottom rows; stated explicitly so the
  override layer is auditable independently of the matrix.
- **O2 (Ask-first, Boundaries §Ask-first)**: `blast_radius == "security-sensitive"`
  ⇒ `auto_apply_allowed: false, human_review_required: true` regardless
  of matrix. The per-edit Confirmation Gate then asks the user.

## Decision Function

```
decide(ec, conf, br, ct):
    if ec is null:                  return {false, true}   # O3
    if ec == "Low-evidence area":   return {false, true}   # O1
    if br == "security-sensitive":  return {false, true}   # O2
    return matrix[(ec, conf)]                              # baseline
```

`change_type` is enumerated in the schema for taxonomic completeness but
does NOT participate in `decide()`. The per-edit Confirmation Gate
retains responsibility for change-type-specific checks.

## Machine-Readable Policy

<!-- machine-readable-policy:v1 -->
```yaml
matrix:
  - evidence_class: "Proven result"
    confidence: high
    auto_apply_allowed: true
    human_review_required: false
  - evidence_class: "Proven result"
    confidence: medium
    auto_apply_allowed: false
    human_review_required: true
  - evidence_class: "Proven result"
    confidence: low
    auto_apply_allowed: false
    human_review_required: true
  - evidence_class: "Engineering guidance"
    confidence: high
    auto_apply_allowed: true
    human_review_required: false
  - evidence_class: "Engineering guidance"
    confidence: medium
    auto_apply_allowed: false
    human_review_required: true
  - evidence_class: "Engineering guidance"
    confidence: low
    auto_apply_allowed: false
    human_review_required: true
  - evidence_class: "Repo default"
    confidence: high
    auto_apply_allowed: true
    human_review_required: false
  - evidence_class: "Repo default"
    confidence: medium
    auto_apply_allowed: false
    human_review_required: true
  - evidence_class: "Repo default"
    confidence: low
    auto_apply_allowed: false
    human_review_required: true
  - evidence_class: "Low-evidence area"
    confidence: high
    auto_apply_allowed: false
    human_review_required: true
  - evidence_class: "Low-evidence area"
    confidence: medium
    auto_apply_allowed: false
    human_review_required: true
  - evidence_class: "Low-evidence area"
    confidence: low
    auto_apply_allowed: false
    human_review_required: true
overrides:
  low_evidence_block: true              # O1
  security_sensitive_ask_first: true    # O2
  null_evidence_class_block: true       # O3
change_types: [formatting, structure, wording, policy, tool-permission, hook, apply-flow]
blast_radii: [single-file, multi-file, runtime-behavior, security-sensitive]
```

## Consumer Workflow

Each apply-* skill must collect three input fields per finding before
calling `decide()`:

1. `evidence_class` — from the finding's evidence label
   (`skills/review-claude-config/references/evidence-contract.md`
   four-class taxonomy)
2. `confidence` — maintainer-assessed confidence in the finding (`high /
   medium / low`)
3. `blast_radius` — scope of impact (`single-file / multi-file /
   runtime-behavior / security-sensitive`)

Call `decide(evidence_class, confidence, blast_radius, change_type)`:

- `auto_apply_allowed: true` → proceed into the per-edit Confirmation
  Gate (skill's existing `## Hard Rules` flow)
- `auto_apply_allowed: false` → route to manual-only handling; do not
  enter the Edit flow regardless of what the per-edit Confirmation Gate
  would say

The policy decides whether to ENTER an Edit; the per-edit Confirmation
Gate (already present in each apply-* SKILL.md `## Hard Rules`) still
runs on every Edit — the two layers compose, the Gate is not replaced.
