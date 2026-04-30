# Legacy FAIL Triage — 2026-04-30

Sample-triage of the top-3 highest-FAIL items surfaced by `scripts/audit_suite.py`
after Phase A (8 new FAILs fixed). Goal: distinguish rubric-calibration issues
from genuine skill defects before bulk-fixing 252 legacy FAILs.

## Method

Per top-FAIL item, sample 3 representative FAIL paths, inspect the trigger
match and the cited reason, and classify the verdict as:

- **A: Rubric over-strict** — false positive; pattern catches valid forms
- **B: Real defect** — skill genuinely lacks the required predicate
- **C: NA-condition missing** — trigger fires on construct that should be exempt

## Findings

### COMP-X (32/33 fails) — VERDICT: A + B (mixed)

Sampled `audit-mcp-auth`, `check-repo-health`, `scaffold-skill`.

| Path | Reason | Class |
|---|---|---|
| `audit-mcp-auth` | "review-skill (audit) missing convergence/grade-distribution/evidence-citation" | **A** — one-time keychain check, not quality-review; misclassified by verb-prefix |
| `check-repo-health` | "review-skill (review) missing …" | **A** — verb is "Verifies", "review" appears only in object-position ("running reviews") |
| `scaffold-skill` | "no explicit success condition" | **B** — scaffold skills genuinely lack `done when` predicate |

**Root cause:** review-skill clause classifier (rubric L137) is too broad:
1. Matches `review|audit|classify|evaluate|score|certify` as substring anywhere in name/description, including object-position mentions
2. Treats every `audit-*` skill as quality-review; `audit-mcp-auth` is a one-time bug detector, not a graded review

**Recommendation:** refine classifier to (a) match primary verb only, (b) maintain explicit allowlist of true review-class skills (review-skill, review-agent, review-rule, review-claude-config, review-analytics, review-session-trace, classify-trace-errors, audit-trust-chain, audit-policy-compliance, audit-memory-hygiene, audit-context-budget). Estimated 50% of COMP-X FAILs flip to PASS after refinement.

### COMP-W (26/33 fails) — VERDICT: A (over-strict)

Sampled `audit-context-budget`, `review-agent`, `scaffold-skill`.

All three trigger on bounded narrative iteration:
- `audit-context-budget`: "For each CLAUDE.md found: count lines matching …" (×7 occurrences)
- `review-agent`: "Repeat for each recommendation, ordered by impact"
- `scaffold-skill`: similar `glob → process each` patterns

These are bounded list-iteration verbs (`glob` provides finite set), not unbounded loops requiring termination predicates. The MAST-F14 motivation (unterminated reasoning) does not apply.

**Recommendation:** narrow COMP-W trigger to (a) require state-mutation context (`while`, `until`, `loop`, `retry`) AND/OR (b) require unbounded-source context (`keep asking`, `iterate over response`, `follow links`). Drop `for each` from trigger entirely (too colloquial). Estimated 80% of COMP-W FAILs flip to NA.

### RL-9b (31/33 fails) — VERDICT: B + A (mixed)

Sampled `audit-memory-hygiene` (PASS — control), `review-session-trace` (FAIL), `audit-policy-compliance` (FAIL).

Both FAIL paths read external content (jsonl transcripts, policy traces) that may contain tokens. Neither has any `redact|truncate|skip` rule. **These are genuine defects (B)** — skills should have credential-scope rules when reading external files.

However, the regex is narrow — many skills probably mention "redact" or "secret" in non-conforming forms. **Possible A-component** for skills that have informal scope rules not matching the strict regex.

**Recommendation:** keep RL-9b regex (the strict form is the point — verifiable redaction). For each FAIL, add explicit credential-scope rule. Estimated 90% of RL-9b FAILs are genuine defects requiring skill edits, not rubric refinement.

## Action Items

| Issue | Type | Effort | Description |
|---|---|---|---|
| New issue (P2) | Rubric refinement | 1 session | COMP-X review-skill classifier — refine to primary-verb-only + allowlist |
| New issue (P2) | Rubric refinement | 1 session | COMP-W trigger — drop `for each`, require state-mutation/unbounded-source context |
| #90 (existing) | Skill defects | 2-3 sessions | RL-9b credential-scope rules for ~25 skills reading external content |

## Total FAIL Reduction Projection

| Item | Current FAILs | Post-refinement (est.) | Method |
|---|---|---|---|
| COMP-X | 32 | 16 (-50%) | Classifier refinement |
| COMP-W | 26 | 5 (-80%) | Trigger narrowing |
| RL-9b | 31 | 3 (-90%) | Skill edits (not rubric) |
| **Subtotal** | **89** | **24** | **-73%** |

The remaining 163 FAILs (CLAR-*, COMP-Z, SP-*, IJ-1b, RL-1b/3b/4b, AH-2b) need
their own sample-triage to determine A/B/C distribution before bulk action.

## Next Step

Commit this triage report, then open the 2 rubric-refinement issues. Skill
defects (RL-9b) deferred to #90 batch session. Rubric refinements must NOT
be done mid-session (cache-prefix freeze per CLAUDE.md) — they are
between-session edits to `scoring-rubric.md`.
