---
last_refreshed: 2026-04-19
---

# Stable Finding Identity and Lifecycle Tracking

## Key Findings

**SARIF v2.1.0** defines `result.fingerprints` (stable, fully-computed) and `result.partialFingerprints` (contributing factors like `primaryLocationLineHash/v1`). Algorithm versioning via `algorithmName/vN` namespace ([OASIS SARIF v2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)).

**SonarQube cascading match:** (1) rule + line number + line hash, (2) rule + moved-block detection, (3) rule + message + line hash, (4) rule + message + line number, (5) rule + line hash only, (6) match against closed issues → reopen ([SonarQube docs v10.1](https://docs.sonarsource.com/sonarqube-server/10.1/user-guide/issues)).

**Core fingerprint pattern:** `fingerprint = f(rule_id, location_hash, content_hash)`. All tools anchor on deterministic rule identifier + location-derived hash. Never include LLM-generated text in hash.

**Baseline diff pattern:**
- `new = current_findings - baseline_findings`
- `recurring = current_findings ∩ baseline_findings`
- `fixed = baseline_findings - current_findings`

**DefectDojo** supports configurable hash fields per scanner via `HASHCODE_FIELDS_PER_SCANNER`. On reimport, unmatched existing findings auto-mitigate ([DefectDojo docs](https://docs.defectdojo.com/en/working_with_findings/finding_deduplication/deduplication_algorithms/)).

**GitHub Code Scanning** computes `primaryLocationLineHash` from source content, combined with `ruleId` and file path ([GitHub SARIF Support](https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning)).

## Recommended Finding-ID Schema

```
finding_id = {checklist_item}:{relative_path}:{dimension}/v1
Example:    WS-2:skills/foo/SKILL.md:Clarity/v1
```

- `checklist_item` = deterministic rule ID (replaces missing "rule catalog" for LLM findings)
- `relative_path` = location anchor
- `dimension` = classification anchor
- `/v1` = algorithm version (SARIF Appendix B pattern)
- Non-checklist findings: `ADHOC:{path}:{dimension}:{slug}/v1`

## Sources

| Claim | Source | Tier |
|-------|--------|------|
| SARIF fingerprint spec | OASIS SARIF v2.1.0 | 1 |
| SonarQube cascading match | SonarQube docs v10.1 | 1 |
| DefectDojo dedup algorithms | DefectDojo docs | 1 |
| GitHub primaryLocationLineHash | GitHub SARIF docs | 1 |
| SemHash semantic dedup | arXiv:2410.01141 | 1 |

---

## Multi-Source Merge Rules (Added 2026-04-19)

*Specification for merging findings produced by multiple LLM perspectives reviewing the same artifact. Feeds P1.1 (multi-perspective review) merge logic.*

### Problem Statement

With three perspectives reviewing the same skill/agent/rule artifact (Clarity, Correctness, Integration), findings frequently describe the same defect through different lenses. A naive line-hash-only match misses cross-perspective overlaps; a naive file-hash-only match over-merges unrelated findings on the same file. We need a layered scheme.

### Dual-Layer Fingerprint

**Layer 1 — exact-merge (SARIF `partialFingerprints`)**

```
partialFingerprints:
  ruleId/v1:                  "<checklist-item-id>"                      // e.g. WS-2
  pathAndDimension/v1:        "<rel-path>:<dimension>"                   // e.g. skills/foo/SKILL.md:Clarity
  primaryLocationLineHash/v1: "<sha256 of the source line-range>"
```

Two findings merge unconditionally when all three `partialFingerprints` match.

**Layer 2 — flag-for-review**

Path + dimension match but line-hash differs:
- Embedding similarity ≥ 0.92 → soft-merge (mark as `auto-merged-by-similarity`).
- Embedding similarity ≥ 0.85 but < 0.92 → flag for manual review (`manual-review-required`).
- Embedding similarity < 0.85 → keep separate.

Embedding similarity is **never** the sole merge criterion. Path + dimension + similarity together.

### Full Merge Pipeline (5 layers)

```
Input: findings_by_perspective = { Clarity: [...], Correctness: [...], Integration: [...] }

Layer 0 (content-dedup, runs first):
  For each pair of findings sharing (path, line-range, ≥80% token-overlap on evidence):
    merge into one finding tagged dimensions = {A, B, ...}

Layer 1 (domain-ownership):
  For each surviving conflict (same partialFingerprint, conflicting recommendations):
    winner = finding from the perspective owning the relevant dimension
      - Safety     → Correctness perspective
      - Clarity    → Clarity perspective
      - Integration / Dependencies → Integration perspective

Layer 2 (weighted vote):
  If no Layer-1 owner: aggregate by confidence-weighted severity vote.
  severity = max(perspective severities)

Layer 3 (deterministic tie-break):
  Lexicographic by perspective name (Clarity < Correctness < Integration).

Layer 4 (manual-review escalation):
  If ≥2 perspectives vote with confidence >0.8 on conflicting actions → flag for human review.
```

### Ownership Assignment Table

| Dimension / checklist prefix | Owner perspective |
|------------------------------|-------------------|
| WS-*, RD-5, PD-1 (structure, readability) | Clarity |
| COMP-X, COMP-Y, COMP-Z, CE-X, SAMP-1, SAMP-2, RD-4, RD-6 (correctness, robustness) | Correctness |
| IJ-*, SP-*, META-1a, META-1b, META-2, META-3a, META-3b (integration, safety-of-chain, metadata) | Integration |

Each sub-agent prompt declares its ownership explicitly and records cross-domain signals with `flag owner_conflict = true` rather than grading them. The orchestrator forwards cross-domain signals to the owning perspective for validation.

### Shared Boundary Exemplars (BARS)

All three perspectives share the same `boundary-exemplars.md` file. Evidence: Behaviorally Anchored Rating Scales research shows shared exemplars reduce rater divergence from 30 % to <5 % vs. per-rater exemplars. Only split per-perspective if pilot convergence fails (≤1-letter grade variance across two runs on unchanged file) — not preemptively.

### SARIF Compatibility Note

The combined `finding_id` recommended in the "Recommended Finding-ID Schema" section above maps cleanly to SARIF `partialFingerprints`:

```
finding_id = "{checklist_item}:{rel_path}:{dimension}/v1"
         ↔ partialFingerprints["pathAndDimension/v1"] + ["ruleId/v1"]
```

SARIF tools can interpret our finding-id schema without loss. Our custom dimension annotation lives in `properties.dimension` — a SARIF-spec-compliant extension slot.

### Sources for This Section

Tier 1:
- [OASIS SARIF v2.1.0 — partialFingerprints spec](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
- [GitHub Code Scanning — SARIF support](https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning) (primaryLocationLineHash convention)
- [SonarQube docs v10.1 — cascading match](https://docs.sonarsource.com/sonarqube-server/10.1/user-guide/issues)

Tier 2:
- [AIHR — BARS overview](https://www.aihr.com/blog/behaviorally-anchored-rating-scale/) — shared-exemplar evidence.
- [NVIDIA NeMo SemDedup](https://docs.nvidia.com/nemo-framework/user-guide/25.07/datacuration/semdedup.html) — threshold-tuning baseline.
