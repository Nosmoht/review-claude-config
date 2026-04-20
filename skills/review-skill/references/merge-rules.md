---
name: merge-rules
description: Deterministic merge rules (Layer 0-4) applied by scripts/merge_findings.py on perspective certificates
last_refreshed: 2026-04-20
---

# Merge Rules

Implemented by `scripts/merge_findings.py`. Referenced by `/review-skill` orchestrator. JIT-loaded — not in shared prefix.

## Inputs

- `clarity.json` — certificate from `review-perspective-clarity`
- `correctness.json` — certificate from `review-perspective-correctness`
- `integration.json` — certificate from `review-perspective-integration`

Each certificate schema:
```json
{
  "perspective": "clarity|correctness|integration",
  "dimensions": {"Clarity": "B", "Completeness": "A", ...},
  "weighted_score": 82.5,
  "artifact_frontmatter": {"allowed_tools": ["Read", "Write", ...]},
  "findings": [
    {
      "id": "WS-2:skills/foo/SKILL.md:Clarity/v1",
      "dimension": "Clarity",
      "checklist_item": "WS-2",
      "severity": "High",
      "primary_focus": true,
      "owner_conflict": false,
      "hint_owner": null,
      "path": "skills/foo/SKILL.md",
      "line_range": "12-14",
      "evidence": "if needed, split the file",
      "why": "...",
      "validation": "...",
      "current": "...",
      "recommended": "..."
    }
  ]
}
```

## Layer 0 — Content dedup

For each pair of findings `(f, g)`:
- Same `path` AND same `line_range` AND `overlap_ratio(f.evidence, g.evidence) >= 0.80` → collapse.
- Collapsed finding carries:
  - `dimensions: sorted(union)` — multi-tagged if different perspectives flagged different dimensions.
  - `perspectives: sorted(union)` — list of source perspectives.
  - `severity: max(SEVERITY_RANK)` — highest of the group.

Tokenizer (deterministic):
```python
tokens = set(re.findall(r"\w+", text.lower()))
overlap = |tokens_a & tokens_b| / max(|tokens_a|, |tokens_b|)
```

## Layer 1 — Owner-weighted dimension grade

Dimension owners:
| Dimension | Owner perspective | Weight |
|-----------|-------------------|--------|
| Clarity | clarity | 2× |
| Completeness | correctness | 2× |
| Prompt Engineering | correctness | 2× |
| Context Engineering | correctness | 2× |
| Goal Alignment | correctness | 2× |
| Safety | integration | 2× |
| Metadata | integration | 2× |

Non-owner perspectives contribute weight 1×. Owner's weight enables the perspective with domain-focus to drive the grade while still allowing sibling signal.

For each dimension:
```
numerics = [(GRADE_TO_NUMERIC[g], p) for each perspective p with grade g]
weighted = multiply each entry by 2 if p is owner, else 1
avg = sum(weighted) / count(weighted)
grade = {A if avg >= 90, B if avg >= 80, C if avg >= 70, D if avg >= 60, else F}
```

## Layer 2 — Max-severity tiebreak

When multiple perspectives emit findings on the same Layer-0 group with different severities, the collapsed finding takes `max(severity)` per rank `High > Medium > Low`.

## Layer 3 — Lexicographic tiebreak

When two findings have identical Layer-0 signature (path + line_range + evidence) AND identical severity AND different perspectives, use lexicographic ordering on perspective name (`clarity < correctness < integration`) to select the primary perspective attribution.

## Layer 4 — Manual-review escalation

When ≥2 perspectives report findings on the same path-and-line with high confidence (severity ∈ {High}) and their `current` / `recommended` blocks contradict, the finding is tagged `manual_review: true` and surfaced in the merged cert's `owner_conflicts` list. Orchestrator emits it to the user's certificate unresolved.

## Degraded mode

If any `{clarity, correctness, integration}.json` is missing or malformed, the merge proceeds with remaining certs and sets:
- `degraded_mode: true`
- `missing_perspectives: [names]`
- Dimensions owned by a missing perspective get grade `F` with `grade_source: ""` (triggers ESC-5).

## Output

Merged JSON (schema — see script source for authoritative fields):
```json
{
  "status": "success|partial|failure",
  "degraded_mode": bool,
  "missing_perspectives": [...],
  "dimensions": {"Clarity": "B", ...},
  "grade_sources": {"Clarity": "clarity", ...},
  "weights": {"Clarity": 0.15, ...},
  "weighted_score": 82.5,
  "findings": [...],
  "owner_conflicts": [...],
  "perspective_scores": {"clarity": 80.0, "correctness": 85.0, "integration": 82.5}
}
```

## Determinism invariant

Given identical input files, Python >= 3.9, `scripts/merge_findings.py` produces byte-identical output. Convergence test on same artifact across two runs must yield same `finding_id` set at High/Medium severity (≤1-letter grade variance permitted only on non-owned dimensions).
