---
generated_by: review-skill
schema_version: 1
date: 2026-04-09
target: /Users/ntbc/workspace/review-claude-config/skills/review-skill/SKILL.md
baseline_version: 2026-04-04
items_reviewed: 1
summary:
  - name: review-skill
    type: Skill
    path: skills/review-skill/SKILL.md
    overall: A
    score: 92.0
    clarity: A
    completeness: B
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
---

### Goal
Evaluates a single Claude Code skill file across 7 evidence-based dimensions and produces an optimization certificate with graded findings and concrete recommendations.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | WS-1/2/3/4 PASS; all phases and conditionals have explicit, observable criteria; RD-5 PASS confirms step-dependency clarity. |
| Completeness | B | 15% | AH-2 FAIL: no default or explicit error defined when $ARGUMENTS is omitted; all other completeness items pass. |
| Prompt Engineering | B | 15% | Structured output template, Evidence-first critique, Constraint Specification (Hard Rules), Verification Criteria present (4 techniques); lacks few-shot examples and role priming. |
| Context Engineering | A | 15% | PD-1/2/3 + RF-1/2/3 PASS; all references JIT-loaded; tool set curation appropriate; Write+WebFetch Tier A justified via Hard Rules scope limit. |
| Goal Alignment | A | 20% | Domain cache CACHED (16 days). Skill covers all quality dimensions of skill evaluation, integrates engineering baseline, domain cache, RD diagnostics, and evidence-first recommendations. |
| Safety | A | 15% | SP-1/2/4 PASS; Write scoped to .claude/reviews/ via Hard Rules; confirmation gate before write; RD-6 PASS (tool availability probed before use). |
| Metadata | A | 5% | Complete frontmatter; verb-first description; RD-1/2/3 all PASS; argument-hint present; allowed-tools matches usage. |
| **Overall** | **A** | **100%** | **Weighted: 92.0 → A** |

### Strengths
- Full-checklist workflow (PD-1 through RD-6) with PASS/FAIL/NA verdict for every item prevents partial evaluations.
- Evidence-first recommendation format (Evidence/Why/Validation/Current/Recommended) produces directly actionable findings.
- Tool availability is probed in Step 0 with graceful degradation paths for every unavailable tool — no silent failures.
- New Reliability Diagnostics section cleanly surfaces RD FAILs as actionable activation/execution risk items, distinct from dimension scoring.

### Reliability Diagnostics

#### Activation
No activation issues detected.

#### Execution
No execution issues detected.

### Recommendations

#### 1. Define behavior for missing $ARGUMENTS (Impact: Low, Category: Workflow)

**Evidence:** Phase "Argument Handling" states "`$ARGUMENTS` is the path to a SKILL.md file" and "Validate the file exists" — no branch defined for empty input.

**Why it matters:** If a user invokes `/review-skill` without a path argument, the skill has no defined fallback. Consistent with AH-2 (Completeness): edge case leaves behavior undefined, though Low impact as interactive use almost always provides the path.

**Validation:** On re-review, AH-2 returns PASS.

**Current:**
```
- `$ARGUMENTS` is the path to a SKILL.md file.
- Validate the file exists and contains YAML frontmatter with a `name` field (required for skills).
- If the file does not look like a skill, report the error and stop.
```

**Recommended:**
```
- `$ARGUMENTS` is the path to a SKILL.md file.
- If `$ARGUMENTS` is empty, prompt the user: "Provide the path to a SKILL.md file to review." and stop.
- Validate the file exists and contains YAML frontmatter with a `name` field (required for skills).
- If the file does not look like a skill, report the error and stop.
```
