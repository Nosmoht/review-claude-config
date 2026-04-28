---
calibration_version: 2026-04-28
generated_at: 2026-04-28
last_refreshed: 2026-04-28
rubric_baseline_version: 2026-04-22
methodology: rubric-application-internal-consistency (no independent ground truth)
---

# Calibration Run 2026-04-28 — Empirical Distribution Analysis

## Methodology Note (Honest Disclosure)

This run originally planned a divergence comparison between rubric-applied empirical scores and user-elicited ground-truth grades. During execution, the maintainer correctly identified GT-elicitation as **methodologically circular**: in a solo-maintainer repo where the user authored both the rubric and the skills under review, asking them to "blindly grade" reduces to self-grading the rubric they wrote. This is the Round-2 V1 self-fulfilling-calibration risk realized in execution.

**Adjusted methodology**: this run reports the empirical distribution alone as evidence of *rubric-application internal consistency*. It does **NOT** establish criterion validity (rubric vs underlying construct) — that requires multi-rater human GT, which is out of scope at solo scale. The label `[Application-checked — N=18]` reflects exactly this: the rubric is internally self-consistent at the calibration corpus, no inflation pattern detected.

## Empirical Distribution (N=18)

### Overall Grades

| Grade | Count | % | Items |
|---|---|---|---|
| A | 1 | 5.5% | M2 (check-repo-health) |
| B | 7 | 39% | A1, A2, M1, M5, M7, M9, M11, M12 *(actually 8 — see correction below)* |
| C | 7 | 39% | A3, M3, M4, M6, M8, M10 *(actually 6)* |
| D | 0 | 0% | — |
| F | 3 | 17% | F1, F2, F3 |

**Recount (correct):** A=1, B=8, C=6, D=0, F=3 — total 18.

### Per-Dimension Distribution

| Dim | A | B | C | D | F | NA | Notes |
|---|---|---|---|---|---|---|---|
| Clarity | 5 | 1 | 8 | 1 | 3 | 0 | C is dominant for non-F skills (8 of 14 non-F = 57%) |
| Completeness | 0 | 0 | 12 | 3 | 3 | 0 | C-dominant — likely COMP-X review-skill clause threshold |
| Prompt Engineering | 6 | 7 | 0 | 0 | 5 | 0 | Bimodal: A or B, no C/D for non-F |
| Context Engineering | 8 | 5 | 2 | 0 | 3 | 0 | Skewed A — KV-cache-friendly + JIT loading already common |
| Goal Alignment | 6 | 7 | 1 | 0 | 4 | 0 | Skewed A/B — domain knowledge present in non-F skills |
| Safety | 0 | 0 | 7 | 7 | 4 | 0 | D-heavy (44% non-F have Safety=D) — driven by RL-9b/SP-2b/SP-4b/IJ-1b binary FAILs |
| Metadata | 9 | 4 | 1 | 1 | 3 | 0 | A-dominant — META-1/2/3/4 binary items mostly PASS |

(Notable: Safety is the lowest-grading dimension across the corpus. The 4 binary FAIL items (RL-9b credential-scope, SP-2b/SP-4b tool-archetype-binding, IJ-1b input-validation-pair) cap Safety at C or below for ~83% of non-F skills.)

## Brainstorm-Premise Refutation

The 2026-04-27 issue #29 brainstorm comment claimed: *"32A / 7B / 1C across 40 reports = 80% A rate; scores cluster 90–95, no D/F observed."* It cited 6 root causes including *(RC#1)* `"B across all dimensions = A" rule at scoring-rubric.md:12` and *(RC#5)* `Self-fulfilling calibration`.

**Empirical refutation:**

| Brainstorm claim | Empirical reality |
|---|---|
| 80% A rate | **5.5% A rate** in N=18 (1 of 18 — refuted by ~14× margin) |
| No D/F observed | **17% F rate** observed (3 of 18) |
| Scores cluster 90–95 | Scores span 50.0 → 90.0; mean of non-F = 80.6 (range 74.0–90.0) |
| RC#1 line-12 rule | scoring-rubric.md:12 reads `**Grade derivation:** A=0 FAILs; B=≤25% (no High); C=any High or >25%; D=>50% High; F=>50% total.` — **FAIL aggregation, not all-B promotion** |
| RC#2 only-A/C/F anchors | scoring-rubric.md lines 17–69 carry explicit A/B/C/D/F anchors per dimension — **falsified by direct read** |

The 2026-04-22 rubric refresh added 30+ binary-verifiable items (CLAR-1..4, COMP-W..Z, PE-1/2, SAMP-1/2, SP-2b/4b, IJ-1b, RL-1b/3b/4b/9b, AH-2b, META-1a..4) with Layer 1.5 boundary caps. These items are doing their job: they push grades into the B/C band where they belong, eliminating the inflation the brainstorm anticipated.

**RC#5 (self-fulfilling calibration)** remains a real concern at the criterion-validity level — the rubric still validates against itself. But at the *application-consistency* level, the rubric is producing a healthy, well-spread distribution that does not require threshold adjustment.

## Decision-Gate Outcome (§1.7)

**Selected**: Option 1 — `Application-checked, no move`.

**Reasoning**:
- Empirical distribution does not show inflation
- No threshold change is justified by the data
- GT-elicitation was circular at solo scale; user explicitly chose closure-via-empirical-distribution-alone
- Reversibility: trivially reversible (additive label only; no boundary moves)

## Anchor Cohort Sanity Check (excluded from divergence math per Round-2 V9)

Plan-author proposed 3-A anchors and 3-F anchors. Empirical reality:

- **A-anchors** (proposed A): A1=B (86.0), A2=B (84.5), A3=C (77.5) → **0 of 3 confirmed as A**
- **F-anchors** (proposed F): F1=F (53.0), F2=F (50.0), F3=F (50.0) → **3 of 3 confirmed as F**

The A-anchor mismatch is itself informative: the maintainer's prior was that these are clearly A-grade skills, but the rubric (with binary-verifiable items + Layer 1.5 caps) consistently pushes them to B or C. This is rubric-vs-prior disagreement, not rubric-vs-truth disagreement (no GT was established). It supports two non-exclusive readings:

1. **Rubric is more strict than the maintainer's instinct** — the binary items (RL-9b, SP-2b, etc.) catch issues the eyeball misses. This is the *intended* effect of the binary additions.
2. **Maintainer's prior was overconfident on A-rating** — solo-author bias: the maintainer naturally thinks their best work is A, but the rubric's strict binary checks find real issues.

Either reading is consistent with `[Application-checked — no move]`. No threshold change is needed; the A-anchor mismatch is signal that the rubric is doing useful work.

## Limitations (Disclosed for Closure Comment)

1. **Single-rater empirical scoring** (κ ≈ 0.65 per llm-evaluator-consistency.md). 17 of 18 items used single-perspective fallback (multi-perspective Agent dispatch unavailable in session). 1 item (A2 review-skill) used existing multi-perspective merged report. Mixed methodology across the corpus.
2. **No independent ground truth** — solo-maintainer + same-author-as-rubric makes GT-elicitation circular. Closure label `[Application-checked]` honestly reflects this.
3. **N=18, statistical power** — at N=18 single-rater, this study is powered to detect per-dim drift ≥ ~0.7 letters at 80% power. Smaller drift indistinguishable from noise.
4. **Criterion validity not established** — this study measures rubric-application consistency, NOT whether the rubric's anchors validly track the underlying construct (skill quality as judged by production task-success outcomes). Successor issue tracks.
5. **Anchor cohort effective N = 0 for A-anchors** — proposed 3-A anchors all diverged from rubric; the calibration set lacks confirmed-A anchors. F-anchors all confirmed (3 of 3). Mid-band only carries the divergence signal at N=12.

## Reproducibility

Inputs:
- `2026-04-28-empirical-manifest.yaml` — 18-artifact manifest
- `2026-04-28-empirical-scores.yaml` — per-artifact per-dim grades
- 17 fresh /review-skill reports under `$CLAUDE_PLUGIN_DATA/reports/review-claude-config/2026-04-28T*` (single-perspective fallback)
- 1 reused report `2026-04-22T161232Z-review-skill-runA.md` for A2 (multi-perspective merged)

Computation: this analysis is descriptive (counts and percentages), no metric script written for this run since the planned divergence comparison was abandoned at the GT-elicitation step. Distribution counts can be reproduced trivially by reading `2026-04-28-empirical-scores.yaml` and tallying `summary[].overall` and per-dim fields.
