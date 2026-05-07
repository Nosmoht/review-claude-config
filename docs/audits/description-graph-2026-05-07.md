---
generated_by: scripts/validate_description_graph.py
generated_at: 2026-05-07T20:38:14Z
repo: Nosmoht/review-claude-config
findings_total: 22
findings_error: 0
findings_warning: 22
flag_rate_pct: 68.2
calibration_outcome: pass
sub_issues_filed: []
sub_issues_capped: 22
sub_issues_manifest_path: .work/issue-217/findings_manifest.json
---

# Description-Graph Self-Audit — 2026-05-07

Produced by `python3 scripts/validate_description_graph.py --repo . --format json`
as part of Phase 3 of the description-quality track (issue #217).

## Summary

| Metric | Value |
|---|---|
| Primitives scanned | 44 |
| Total findings | 22 |
| Errors | 0 |
| Warnings | 22 |
| Flag rate (primitives with ≥1 finding) | 68.2% (30 / 44) |
| Calibration threshold | ≥30% |
| Calibration outcome | PASS |

## Check Breakdown

| Check | Count | Severity |
|---|---|---|
| `reciprocal_asymmetry` | 19 | warning |
| `cluster_conflict` | 3 | warning |
| `f_grade` | 0 | — |
| `aggregate_budget_warn` | 0 | — |
| `aggregate_budget_error` | 0 | — |
| `name_collision` | 0 | — |

## Cluster Conflicts

Three genuine semantic clusters were detected (cosine ≥ 0.85 threshold):

1. **classify-trace-errors / review-session-trace** (max cosine=0.900)
   — Both skills analyse session traces; descriptions share heavy overlap.
   Paths: `skills/classify-trace-errors/SKILL.md`, `skills/review-session-trace/SKILL.md`

2. **review-agent / review-rule / review-skill** (max cosine=0.887)
   — Three peer-review skills share structurally identical description templates.
   Paths: `skills/review-agent/SKILL.md`, `skills/review-rule/SKILL.md`, `skills/review-skill/SKILL.md`

3. **review-perspective-clarity / review-perspective-correctness / review-perspective-integration** (max cosine=0.917)
   — Perspective agents share nearly identical descriptions by design (same template).
   Paths: `agents/review-perspective-clarity.md`, `agents/review-perspective-correctness.md`, `agents/review-perspective-integration.md`

## Reciprocal Asymmetry

19 one-directional cross-reference pairs detected. A skill mentions `use X` or `do not use Y; use X`
in its description, but X's description does not mention the source skill in return.

## Sub-Issue Filing: CAP EXCEEDED

`filtered_count = 22 > cap = 15`

Per plan §8 step 4: sub-issues NOT filed automatically. Manifest written to
`.work/issue-217/findings_manifest.json`. Operator should review the manifest
and select top-N findings to file manually via:

```bash
gh issue create \
  --repo Nosmoht/review-claude-config \
  --label "category: description-quality" \
  --title "<check> in <path>" \
  --body "<body per plan §8 template>"
```

Refer to `.work/issue-217/findings_manifest.json` for the full indexed list.

## Reproducer

```bash
python3 scripts/validate_description_graph.py --repo . --format json
python3 scripts/validate_description_graph.py --repo . --format text
```

## Phase Context

- Phase 1a — description-design-problem reference: #215 (closed)
- Phase 1b — empirical anchors in baseline: #223 (closed, superseded)
- Phase 2 — DQ-1..DQ-6 sub-rubric + convention update: #216 (closed)
- Phase 3 — this validator: #217
- Phase 4 — per-primitive DQ scoring + skill wrapper: #218
- Phase 5 — audit-undertriggering skill + eval-cases: #219
