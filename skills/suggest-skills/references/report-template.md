---
name: report-template
description: Report body and frontmatter template for the suggest-skills skill output — use as structure for the presented report and persisted file
last_refreshed: 2026-04-06
---

## Report Body

```
# Skill Suggestions Report

## Repository Overview

- **Target:** [absolute path]
- **Repository Type:** [Application / Skills-Config / Mixed]
- **Tech Stack:** [detected languages, frameworks, infrastructure — or "N/A (skills/config repository)" if no source code]
- **Existing Skills:** [count] ([list names])
- **Suggestions Generated:** [count]

## Suggestions

### 1. [skill-name] (Priority: [High/Medium], Score: [N]/9)

**Evidence Class:** [Proven result / Engineering guidance / Repo default / Low-evidence area]
**Confidence:** [High/Medium/Low]
**Signal Sources:**
- [signal 1 with category reference]
- [signal 2 with category reference]

**Extraction Criteria:** [N/4 passed] — [list which passed]

**Rationale:** [why this skill adds value, with web evidence]

**Skeleton SKILL.md:**
```yaml
[skeleton — explicitly marked as starting point, not production-ready]
```

**Recommended Reference Files:**
- references/[file].md — [purpose]

---

[Repeat for each suggestion, ordered by priority score descending]

## Signal Summary

| Discovery Method | Suggestions |
|-----------------|-------------|
| Layer 1: Table matches | [N] |
| Layer 2: Open reasoning | [N] |
| **Total (after dedup)** | **[N]** |

## Integration Notes

- Suggestions that complement existing skills: [list relationships]
- Suggested implementation order: [highest impact first, with rationale]
```

## Frontmatter

```yaml
---
generated_by: suggest-skills
schema_version: 1
date: YYYY-MM-DD
target: /absolute/path/to/target
repo_type: Application | Skills-Config | Mixed
existing_skills: N
suggestions:
  - name: skill-name
    priority: High
    score: 8
    evidence_class: Engineering guidance
    confidence: Medium
    signal_sources: ["Documentation", "CI/CD"]
    criteria_passed: 4
---
```
