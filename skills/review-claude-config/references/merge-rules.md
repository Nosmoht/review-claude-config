---
name: merge-rules
description: Deterministic merge rules (Layer 0-4 + binary boundary caps) applied by scripts/merge_findings.py on perspective certificates
last_refreshed: 2026-04-22
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

## Layer 1.5 — Binary Boundary Caps

Read after Layer 1 computes owner-weighted dimension grades. Applies deterministic grade caps from `binary_verdicts.json` (produced by `scripts/rubric_binary_evaluator.py` pre-dispatch, step b.0 in `/review-skill` Phase 2b).

**Monotone:** caps only downgrade; never raise a grade.
**Idempotent:** repeated application converges (capped grade is fixed point).

Cap table (each row: FAIL on `item` caps `dimension` at `cap_grade`):

| Item | Dimension | Cap | Rubric source |
|---|---|---|---|
| CLAR-1 / CLAR-2 / CLAR-3 / CLAR-4 | Clarity | C | §Ambiguity Markers grade boundary |
| COMP-W | Completeness | C | §Verification Criteria (MAST-F14) |
| AH-2b | Completeness | C | §Argument Handling grade boundary |
| CE-X | Context Engineering | C | §Observation-Masking Parity gate |
| PE-1 / PE-2 | Prompt Engineering | C | §Reasoning-Model Anti-Patterns |
| SAMP-1 | Prompt Engineering | C | §Sampling-Param Migration |
| SAMP-2 | Metadata | **F** | §Sampling-Param Migration (runtime 400 on Opus 4.7) |
| META-2 | Metadata | C | §Trigger-Consistency grade boundary |
| META-4 | Metadata | C | §Trigger-Consistency (third-person discovery risk) |
| SP-2b / SP-4b / IJ-1b | Safety | C | §Tool-Grant Alignment grade boundary |
| RL-1b / RL-3b / RL-4b / RL-9b | Safety | C | §Agentic Reliability Binary Items grade boundary |

Caps not covered here (e.g. the narrative META-1 = D/F rule requiring META-1a AND META-1b joint FAIL) are NOT applied deterministically when only one half of the OR-pair is binary-evaluated; they remain perspective-owned.

Python reference: `scripts/merge_findings.py` `layer1_5_binary_boundary_cap()`.

## Binary Finding Synthesis

For each item with `verdict == "FAIL"` in `binary_verdicts.json`, `synthesize_binary_findings()` emits one High-severity finding with:

- `id = "{item_id}:{artifact_path}:{dimension}/v1"` — byte-identical across runs (Jaccard=1.0 on binary subset by construction).
- `perspective = "binary-evaluator"` — synthetic source, distinct from `clarity|correctness|integration`.
- `primary_focus = true`, `owner_conflict = false`, `hint_owner = null`.
- `evidence` — composed from evaluator output (`line`, `match`, `trigger`, `missing`, `reason`).
- `current` — evidence text (anchor for `/apply-skill-review-findings` manual-only routing).
- `recommended` — pointer to the BOUNDARY PASS exemplar in `scoring-rubric.md`.

Ordered deterministically by `id` for byte-stable output.

## Convergence Policy

`/review-skill` guarantees Jaccard = 1.0 on H+M finding_ids for the **deterministic subset** only:

- `BINARY_ITEM_IDS` — synthesized from `binary_verdicts.json` with byte-identical `id = "{item_id}:{artifact_path}:{dimension}/v1"`.
- `NARRATIVE_PARENT_IDS` — dropped pre-dedup so supersedence is deterministic.

Findings outside this subset (advisory items like `WS-1`, `OF-3`, `OF-4`, `PE-4`, `CE-3`, `PD-1`, `RF-1`, etc.) are emitted by perspective Haiku agents and may vary run-to-run. They surface in the merged cert at **Low severity** (demoted from whatever the perspective reported — see §"Perspective Finding Handling") and are **advisory** under the convergence gate: they do not block iteration and they do not appear at H+M so Jaccard on H+M is = 1.0 by construction.

Downstream consumers (`/apply-skill-review-findings`, `/review-analytics`, `/check-repo-health` freshness) MUST treat advisory findings as non-blocking. Deterministic findings (synthesized or narrative-parent-dropped) carry the convergence guarantee.

## Perspective Finding Handling

Before Layer 0 dedup, `merge_directory()` applies two rules to perspective-emitted findings:

**1. Drop** — when the finding's `checklist_item` is in the deterministic subset:

- The 28 binary items (`BINARY_ITEM_IDS`, declared in `skills/review-skill/references/merge-policy.yaml`; human-readable enumeration in `scoring-rubric.md` §"Item Inventory" + §"Grade Caps") — prevents double-counting with synthesized findings.
- The 14 narrative parents the rubric supersedes (`NARRATIVE_PARENT_IDS`: `AH-2, IJ-1, META-1, META-2, META-3, RD-5, RL-1, RL-3, RL-4, RL-9, SP-2, SP-4, WS-2, WS-4`) — prevents Haiku-class perspective agents from re-litigating rubric-superseded surface.

Counted in `dropped_perspective_findings`.

**2. Demote** — when the finding is NOT in the deterministic subset AND its severity is `High` or `Medium`, force `severity = "Low"` (issue #72). This keeps advisory findings visible for reviewer triage while removing them from the H+M convergence-blocking surface. Advisory `Low` findings pass through unchanged.

Counted in `demoted_perspective_findings`.

**Fail-safe:** when `apply_caps` is False (binary evaluator missing/malformed/crashed, see §"Missing or malformed `binary_verdicts.json`"), **neither rule fires** — perspectives retain full authority over their findings. Rationale: if the deterministic-subset classification cannot be applied consistently, treating any finding as "advisory" would silently downgrade what may be genuine High-severity signals.

## Missing or malformed `binary_verdicts.json`

If `binary_verdicts.json` is absent, malformed, or has top-level `status == "crashed"`:

- `binary_evaluator_status` recorded as `"missing" | "malformed" | "crashed"`.
- Layer 1.5 is skipped entirely (`boundary_caps_applied: []`).
- Perspective findings on binary/narrative-parent items are **NOT** dropped (fail-safe: evaluator silent ≠ perspective wrong).
- `synthesize_binary_findings()` emits nothing.

If `status == "error"` (evaluator exit 2 with `runner_error > 0`), verdicts are still trusted — items that actually ran produce verdicts and caps; items that runner-errored silently degrade to NA per the evaluator contract.

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
  "perspective_scores": {"clarity": 80.0, "correctness": 85.0, "integration": 82.5},
  "binary_evaluator_status": "present|missing|malformed|crashed|error",
  "binary_verdicts_applied": {"CLAR-2": "FAIL", "META-4": "PASS", ...},
  "boundary_caps_applied": [{"item": "CLAR-2", "dimension": "Clarity", "cap_grade": "C", "grade_before_cap": "A", "applied": true}, ...],
  "dropped_perspective_findings": 2,
  "demoted_perspective_findings": 5
}
```

## Determinism invariant

Given identical input files, Python >= 3.9, `scripts/merge_findings.py` produces byte-identical output **on the deterministic subset** (binary-synthesized + narrative-parent-dropped). Convergence test on same artifact across two runs must yield identical `finding_id` set at High/Medium severity **for items in the deterministic subset only**, per §"Convergence Policy" above. Advisory findings may vary; ≤1-letter grade variance permitted only on non-owned dimensions.
