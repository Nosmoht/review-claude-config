---
last_refreshed: 2026-04-14
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
