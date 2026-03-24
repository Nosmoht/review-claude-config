---
generated_by: review-claude-config
schema_version: 1
date: 2026-03-24
target: /Users/ntbc/workspace/claude/review-claude-config
baseline_version: 2026-03-24
items_reviewed: 2
summary:
  - name: review-claude-config
    type: Skill
    path: .claude/skills/review-claude-config/SKILL.md
    overall: A
    score: 93.5
    clarity: A
    completeness: A
    prompt_engineering: A
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: B
  - name: refresh-engineering-baseline
    type: Skill
    path: .claude/skills/refresh-engineering-baseline/SKILL.md
    overall: C
    score: 76.8
    clarity: B
    completeness: C
    prompt_engineering: C
    context_engineering: B
    goal_alignment: C
    safety: C
    metadata: B
---

# Review Report — 2026-03-24

**Target:** /Users/ntbc/workspace/claude/review-claude-config
**Baseline version:** 2026-03-24
**WebSearch:** Available

---

## 1. review-claude-config (Skill)

**Path:** `.claude/skills/review-claude-config/SKILL.md`

### Goal
Orchestrate automated quality evaluation of all Claude Code skills and agents in a project, producing per-item graded certificates with concrete optimization recommendations based on an evidence-backed rubric and engineering baseline.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Explicit phased workflow (Setup, Discovery, Analysis, Presentation) with deterministic sequencing, parallel batching rules, and clear conditional logic. |
| Completeness | A | 15% | Covers edge cases (no `.claude/` dir, WebSearch unavailable, agent failure), defines output format precisely, includes error handling and stop conditions. |
| Prompt Engineering | A | 15% | Uses role priming, structured output template with exact format, chain-of-thought (Step A then Step B), constraint specification (Hard Rules), and template with placeholders. |
| Context Engineering | A | 15% | Exemplary: JIT retrieval via reference files, subagent isolation, byte-identical shared prefix for KV-cache, batched parallelism, progressive disclosure. |
| Goal Alignment | A | 20% | Multi-dimensional rubric, domain-specific research via WebSearch, concrete rewrites not just commentary, cross-cutting pattern analysis. |
| Safety | A | 10% | Read-only by design with explicit hard rule; tool set excludes Write/Bash/Edit; no destructive operations possible. |
| Metadata | B | 10% | Complete frontmatter, correct tool list, argument-hint present. Description could more precisely mention rubric-based A-F grading for skill selection. |
| **Overall** | **A** | **100%** | Weighted: 93.5 |

### Strengths
- **Exemplary context engineering.** Byte-identical shared prefix for KV-cache, subagent isolation, reference file separation, and batched parallelism.
- **Robust completeness.** Handles WebSearch unavailability, empty discovery, agent failures, and monorepo structures.
- **Concrete output specification.** The analysis agent prompt template leaves no ambiguity; requiring concrete rewrites is a strong quality forcing function.

### Recommendations

#### 1. Add Explicit Scoring Calculation Method (Impact: Medium)
The certificate shows an "Overall" grade but never specifies how to calculate it from individual grades. Two models could produce different overall grades from the same per-dimension scores.

**Current:**
```
| **Overall** | **[A-F]** | **100%** | |
```

**Recommended:**
```
| **Overall** | **[A-F]** | **100%** | [Weighted average] |

Calculate overall grade: convert A=95, B=85, C=75, D=65, F=50, multiply each
by its weight, sum, then map back: >=90 A, >=80 B, >=70 C, >=60 D, <60 F.
```

#### 2. Specify Discovery Agent Return Size Constraint (Impact: Medium)
The Discovery Agent returns full content for every item. In a large monorepo this could bloat the orchestrator's context, contradicting the skill's own context engineering principles.

**Current:**
```
For each discovered file:
- Read the full content
- Classify as "Skill" or "Agent"
- Return: file path, type, full content
```

**Recommended:**
```
For each discovered file:
- Read the full content
- Classify as "Skill" or "Agent"
- Return: file path, type, full content

If total discovered content exceeds 50K tokens, return file path and type only.
The analysis agents will read file content directly via their own Read tool.
```

#### 3. Add Analysis Agent Tool List (Impact: Low)
The analysis agent prompt does not specify which tools it has. Since it needs WebSearch and potentially Read, the tool set should be explicit.

**Current:**
```
You are evaluating a Claude Code [Skill/Agent] for quality.
```

**Recommended:**
```
You are evaluating a Claude Code [Skill/Agent] for quality.

Tools available: WebSearch (for domain research), Read (for reference files).
Do not use any other tools.
```

#### 4. Sharpen Metadata Description (Impact: Low)

**Current:**
```
description: >
  Analyze and optimize all Claude Code skills and agents in a project's .claude/
  directory. Applies evidence-based prompt and context engineering evaluation,
  produces per-item quality certificates with concrete optimization
  recommendations.
```

**Recommended:**
```
description: >
  Audit all Claude Code skills and agents in a project's .claude/ directory.
  Grades each item A-F across 7 dimensions (clarity, completeness, prompt
  engineering, context engineering, goal alignment, safety, metadata) using a
  structured rubric. Produces per-item quality certificates with concrete
  rewrite recommendations.
```

---

## 2. refresh-engineering-baseline (Skill)

**Path:** `.claude/skills/refresh-engineering-baseline/SKILL.md`

### Goal
Automate periodic refresh of a curated prompt/context engineering baseline file using web research, maintaining structure and token budget constraints.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | B | 15% | Clear 5-step workflow. Minor ambiguity: "adapt based on current year" is vague; step 3 redundantly re-reads the baseline already loaded in step 1. |
| Completeness | C | 15% | Happy path is solid. Missing: WebSearch failure handling, conflict resolution for contradictory findings, no backup/rollback before overwriting. The 3-month freshness gate in the description is never enforced in the workflow. |
| Prompt Engineering | C | 15% | Uses chain-of-thought and constraint specification. Missing: no output format template for the change report, no few-shot example of a merged technique entry, no role priming. Merge logic lacks explicit decision criteria. |
| Context Engineering | B | 15% | Minimal 4-tool set, JIT retrieval via Glob then Read, respects 2K token budget. Minor issue: 5 web searches could flood context with no guidance on per-search retention. |
| Goal Alignment | C | 20% | Achieves basic refresh but misses domain-critical practices: no cross-validation of findings, no freshness gate enforcement, no source quality criteria beyond "discard marketing content." |
| Safety | C | 15% | Has Write tool and overwrites a file with no backup, no confirmation gate, and no diff preview. Hard Rules provide some guardrails but no mechanism prevents accidental data loss. |
| Metadata | B | 5% | Complete frontmatter, accurate description, correct tool list. `disable-model-invocation: true` is appropriate. |
| **Overall** | **C** | **100%** | Weighted: 76.8 |

### Strengths
- **Well-structured sequential workflow** — The 5-step process is logical and covers the full lifecycle from locate to report.
- **Token budget awareness** — The 2K constraint with prioritization guidance shows good context engineering discipline.
- **Conservative removal policy** — "Do not remove unless evidence shows they are wrong" protects against information loss.
- **Minimal tool set** — Four tools, each clearly needed, no overlap.

### Recommendations

#### 1. Add User Confirmation Gate Before Write (Impact: High)
The skill overwrites a file that feeds into automated evaluation with no preview or confirmation.

**Current:**
```
### 4. Write the updated file

Update `engineering-baseline.md` with:
- Set `last_refreshed` in frontmatter to today's date
```

**Recommended:**
```
### 5. Preview and confirm

Before writing, show the user a structured change report:
- Techniques to ADD (with source)
- Techniques to UPDATE (with old vs. new)
- Techniques to REMOVE (with justification)

Ask: "Apply these changes to engineering-baseline.md? (yes/no)"
If no, stop and preserve the current file.

### 6. Write the updated file
(proceed only after user confirmation)
```

#### 2. Add Freshness Gate (Impact: High)
The description says "Use when older than 3 months" but the workflow never enforces this.

**Current:**
```
Read the current file content and note the `last_refreshed` date.
```

**Recommended:**
```
Read the current file content and extract the `last_refreshed` date.
If `last_refreshed` is less than 90 days ago, tell the user the baseline
is still current (show the date) and ask whether they want to proceed anyway.
Stop unless they confirm.
```

#### 3. Add Source Quality Criteria and Cross-Validation (Impact: Medium)

**Current:**
```
For each search, extract only actionable techniques with evidence. Discard
marketing content, opinion pieces without evidence, and duplicate information.
```

**Recommended:**
```
For each search, extract only actionable techniques with evidence. Apply these
source quality filters:
- **Accept:** Official documentation (Anthropic, OpenAI, Google DeepMind),
  peer-reviewed research, documented production systems
- **Discard:** Marketing content, opinion without evidence, duplicates, sources
  older than 18 months
- **Cross-validate:** A new technique must appear in 2+ independent credible
  sources or come from a primary vendor source with concrete evidence
```

#### 4. Add Output Format Template for Change Report (Impact: Medium)

**Current:**
```
Tell the user:
- How many new techniques were added
- How many existing techniques were updated
- What was removed (if anything)
- The new `last_refreshed` date
```

**Recommended:**
```
## Baseline Refresh Report — YYYY-MM-DD
| Action | Count |
|--------|-------|
| Added | N |
| Updated | N |
| Removed | N |
| Unchanged | N |
| Token count | NNNN / 2000 |

### Added
- **[Technique]** — [Description]. Source: [citation]
### Updated
- **[Technique]** — Changed: [what]. Source: [citation]
### Removed
- **[Technique]** — Reason: [why]
```

#### 5. Add WebSearch Failure Handling (Impact: Low)
Add to Hard Rules:
```
- If WebSearch is unavailable, stop and report the failure.
- If fewer than 3 of 5 queries return useful results, warn the user.
- If no queries return useful results, leave the baseline unchanged.
```

---

## Summary

| Item | Type | Overall | Clarity | Completeness | PE | CE | Goal | Safety | Meta |
|------|------|---------|---------|--------------|----|----|------|--------|------|
| review-claude-config | Skill | **A** | A | A | A | A | A | A | B |
| refresh-engineering-baseline | Skill | **C** | B | C | C | B | C | C | B |

## Cross-Cutting Observations

- **Consistent strength: tool set curation.** Both skills use minimal, well-scoped tool lists with clear purpose for each tool.
- **Gap in refresh-engineering-baseline.** The review skill is exemplary (A overall), but the refresh skill has several C-grade dimensions that could undermine the quality of the baseline it maintains — which in turn affects review quality. This is the highest-priority area for improvement.
- **Missing confirmation gates.** The refresh skill writes files without user confirmation or backup. Adding a preview + confirm step would raise both Safety and Completeness.
- **No shared error handling pattern.** The review skill handles errors well; the refresh skill doesn't address WebSearch failures. A CLAUDE.md guideline like "all skills with WebSearch must handle search failures gracefully" would help.
- **Output format templates.** The review skill excels here; the refresh skill should adopt the same discipline for its change report.
