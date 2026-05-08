---
generated_by: scripts/validate_description_graph.py
generated_at: 2026-05-07T20:38:14Z
repo: Nosmoht/review-claude-config
findings_total: 22
findings_error: 0
findings_warning: 22
flag_rate_pct: 68.2
calibration_outcome: pass
sub_issues_filed: [228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249]
sub_issues_capped: 0
sub_issues_manifest_path: null
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

## Sub-Issue Filing: CAP-OVERRIDE APPROVED — All 22 Filed

`filtered_count = 22 > cap = 15` triggered the plan §8 step 4 HALT gate.
Operator (2026-05-08) reviewed the manifest and approved filing all 22
findings (3 cluster_conflict + 19 reciprocal_asymmetry, all severity=warning,
zero errors). Issues filed via `mcp__github__issue_write`:

| # | Check | Primitives |
|---|---|---|
| #228 | reciprocal_asymmetry | apply-audit-findings → apply-review-findings |
| #229 | reciprocal_asymmetry | audit-context-budget → audit-repo |
| #230 | reciprocal_asymmetry | audit-mcp-auth → review-mcp-server |
| #231 | reciprocal_asymmetry | audit-memory-hygiene → review-claude-md |
| #232 | reciprocal_asymmetry | check-repo-health → review-claude-config |
| #233 | reciprocal_asymmetry | develop-hooks → scaffold-rule |
| #234 | reciprocal_asymmetry | refresh-evidence-coverage → audit-context-budget |
| #235 | reciprocal_asymmetry | review-analytics → check-repo-health |
| #236 | reciprocal_asymmetry | review-claude-config → review-skill |
| #237 | reciprocal_asymmetry | review-claude-md → review-skill |
| #238 | reciprocal_asymmetry | review-domain-currency → review-skill |
| #239 | reciprocal_asymmetry | review-rule → review-skill |
| #240 | reciprocal_asymmetry | review-skill → apply-skill-review-findings |
| #241 | reciprocal_asymmetry | run-eval-cases → review-claude-config |
| #242 | reciprocal_asymmetry | scaffold-rule → scaffold-skill |
| #243 | reciprocal_asymmetry | suggest-skills → review-claude-config |
| #244 | reciprocal_asymmetry | validate-primitive-dependencies → review-claude-config |
| #245 | reciprocal_asymmetry | maintain-evidence-layer → review-claude-config |
| #246 | reciprocal_asymmetry | sync-research-index → review-claude-config |
| #247 | cluster_conflict | classify-trace-errors ↔ review-session-trace (cosine 0.900) |
| #248 | cluster_conflict | review-agent ↔ review-rule ↔ review-skill (cosine 0.887) |
| #249 | cluster_conflict | review-perspective-{clarity,correctness,integration} (cosine 0.917) |

All issues carry label `category: description-quality`. None auto-staged
`status: ready` — they remain discovery artifacts pending triage.

Refer to `.work/issue-217/findings_manifest.json` for the original indexed
list; that file is preserved as the audit-time snapshot of validator output.

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
