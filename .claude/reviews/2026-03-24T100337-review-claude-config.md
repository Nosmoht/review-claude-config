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
    safety: B
    metadata: A
  - name: refresh-engineering-baseline
    type: Skill
    path: .claude/skills/refresh-engineering-baseline/SKILL.md
    overall: A
    score: 93.0
    clarity: A
    completeness: A
    prompt_engineering: A
    context_engineering: B
    goal_alignment: A
    safety: A
    metadata: B
---

# Review Report — 2026-03-24T100337

## Item 1: review-claude-config

**Type:** Skill | **Path:** `.claude/skills/review-claude-config/SKILL.md`

### Goal
Orchestrate automated quality audits of Claude Code skills and agents by applying a structured rubric and engineering baseline, producing per-item quality certificates with actionable optimization recommendations.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Explicit 4-phase sequential workflow with numbered steps, deterministic behavior, and clear conditional logic. |
| Completeness | A | 15% | Edge cases handled (no .claude/ found, no items, WebSearch unavailable, agent failure), output format fully specified with template. |
| Prompt Engineering | A | 15% | Structured output template, role priming in analysis agent, chain-of-thought (Step A→B), few-shot grade calculation example, explicit constraints (Hard Rules). |
| Context Engineering | A | 15% | JIT retrieval, subagent isolation, reference file separation, KV-cache optimization (byte-identical prefix), batched parallelism. |
| Goal Alignment | A | 20% | Multi-dimensional rubric matches LLM-as-judge research, concrete rewrites required, report persistence for tracking improvement. |
| Safety | B | 15% | Read-only hard rule, confirmation gate before writing, analysis agents restricted to WebSearch+Read. Grep listed in allowed-tools but never used. |
| Metadata | A | 5% | Complete frontmatter with name, description, argument-hint, and allowed-tools. Description accurately reflects the audit workflow. |
| **Overall** | **A** | **100%** | **Weighted: 93.5** |

### Strengths
- Exceptionally well-structured 4-phase workflow with clear phase boundaries, parallel execution, and deterministic behavior.
- Sophisticated context engineering: byte-identical shared prefixes for KV-cache, subagent isolation with restricted tool sets, JIT reference loading, batched parallelism.
- Analysis agent prompt template is a standout: role priming, structured output, chain-of-thought, few-shot example, and explicit constraints in one coherent template.

### Recommendations

#### 1. Remove Grep from allowed-tools (Impact: Medium)
Grep is listed but never referenced in the workflow. Violates tool set curation principle.

**Current:**
```
allowed-tools: Agent, Read, Write, Glob, Grep, WebSearch
```

**Recommended:**
```
allowed-tools: Agent, Read, Write, Glob, WebSearch
```

#### 2. Add Few-Shot Threshold Examples to Analysis Agent Prompt (Impact: Medium)
LLM-as-judge research recommends boundary-case examples between grade levels for grading consistency, not just arithmetic examples.

**Current:**
```
Example (no Write/Bash/Edit): Clarity=A(95), Completeness=B(85), PE=B(85),
CE=A(95), Goal=B(85), Safety=A(95), Meta=B(85).
Score = 95×.15 + 85×.15 + 85×.15 + 95×.15 + 85×.20 + 95×.10 + 85×.10 = 89.0 → B
```

**Recommended:**
```
### Grade Calculation Example
(no Write/Bash/Edit): Clarity=A(95), Completeness=B(85), PE=B(85),
CE=A(95), Goal=B(85), Safety=A(95), Meta=B(85).
Score = 95×.15 + 85×.15 + 85×.15 + 95×.15 + 85×.20 + 95×.10 + 85×.10 = 89.0 → B

### Grading Boundary Examples

**Clarity B vs C:** B has a clear workflow where step order is unambiguous but
one conditional ("if needed") lacks criteria. C has steps that two models would
sequence differently because dependencies between steps are not explicit.

**Safety B vs C:** B restricts tools to what's needed and includes a confirmation
gate before writes. C has tools broader than needed (e.g., Bash when only Read
is required) or could modify user files without explicit confirmation.
```

#### 3. Specify Maximum Report Size for Large Codebases (Impact: Low)
No guidance on total report size for monorepos with 50+ items.

**Current:**
```
**Body:** All per-item reports (Goal + Certificate + Strengths + Recommendations),
Summary Table, Cross-Cutting Observations.
```

**Recommended:**
```
**Body:** All per-item reports (Goal + Certificate + Strengths + Recommendations),
Summary Table, Cross-Cutting Observations.

**Large codebase handling:** If more than 20 items are reviewed, include full
per-item reports only for items scoring C or below. A/B items get a one-line
summary row only. All items are still analyzed and included in the Summary Table
and frontmatter summary.
```

#### 4. Add Inter-Run Delta Comparison (Impact: Low)
Supports the "iterate until convergence" workflow by comparing grades across runs.

**Current:**
```
Timestamp ensures each run produces a unique file, supporting the "iterate until
convergence" workflow.
```

**Recommended:**
```
Insert a new Step 3 (before Confirm) in Phase 4:

### Step 3: Delta comparison
If a previous review report exists in `<target>/.claude/reviews/`:
- Read the most recent prior report's frontmatter summary
- Compare each item's current grades against prior grades
- Append a Delta section to the report body

If no prior report exists, skip this step.
```

#### Reference File Recommendation
The reference file architecture is already well-implemented. No additional reference files needed.

---

## Item 2: refresh-engineering-baseline

**Type:** Skill | **Path:** `.claude/skills/refresh-engineering-baseline/SKILL.md`

### Goal
Maintain a curated, evidence-based engineering reference file by systematically searching for current best practices and merging validated findings into an existing baseline document.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Explicitly sequential 7-step workflow with deterministic branching at every decision point (freshness gate, search failures, user confirmation). |
| Completeness | A | 15% | Edge cases well-covered: file not found, freshness gate, three tiers of WebSearch degradation, user decline, token budget. Minor gap: no handling for corrupted frontmatter. |
| Prompt Engineering | A | 15% | Role priming ("research librarian"), structured output template (Step 7), chain-of-thought merge example (Step 4), constraint specification (Hard Rules). 5+ techniques used effectively. |
| Context Engineering | B | 15% | Minimal 4-tool set, JIT retrieval, token budget. Deductions: Glob unnecessary (hardcoded path), all 5 queries always run without early termination. |
| Goal Alignment | A | 20% | Strong domain alignment: source quality criteria match evidence synthesis standards, conservative merge logic, human confirmation gate, structured change reporting. |
| Safety | A | 15% | Confirmation gate before writes, multiple stop conditions, conservative defaults ("leave baseline unchanged"), token budget prevents runaway growth. |
| Metadata | B | 5% | Complete frontmatter, description accurate, tool list matches usage. `disable-model-invocation` purpose not obvious from skill body. |
| **Overall** | **A** | **100%** | **Weighted: 93.0** |

### Strengths
- Excellent safety design with multiple stop conditions and conservative defaults — the baseline is never modified without explicit user approval.
- Source quality criteria (credible, actionable, cross-validated) are rigorous and well-specified, matching evidence synthesis best practices.
- The merge decision example in Step 4 effectively demonstrates expected reasoning for update vs. remove decisions.

### Recommendations

#### 1. Remove Glob from allowed-tools (Impact: Medium)
The file path is hardcoded in Step 1. Read with error handling achieves the same result with one fewer tool.

**Current:**
```
allowed-tools: WebSearch, Read, Write, Glob
```

**Recommended:**
```
allowed-tools: WebSearch, Read, Write
```

And update Step 1:
**Current:**
```
Use Glob to find the engineering-baseline.md file:
- `.claude/skills/review-claude-config/references/engineering-baseline.md`
- If not found, report the error and stop.
```

**Recommended:**
```
Read `.claude/skills/review-claude-config/references/engineering-baseline.md`.
If the file is not found, report the error and stop.
```

#### 2. Add Missing-Frontmatter Handling (Impact: Medium)
Step 2 assumes `last_refreshed` exists. Add a branch for missing/unparseable frontmatter.

**Current:**
```
Read the current file content and extract the `last_refreshed` date from frontmatter.
```

**Recommended:**
```
Read the current file content and extract the `last_refreshed` date from frontmatter.
If `last_refreshed` is missing or unparseable, treat the baseline as stale and
proceed directly to Step 3.
```

#### 3. Add Adaptive Search Termination (Impact: Low)
Allow early termination of the 5 queries if findings are already saturated.

**Current:**
```
Run these WebSearch queries (replace `[current year]` with the actual year):
```

**Recommended:**
```
Run these WebSearch queries (replace `[current year]` with the actual year).
After each query, check if new actionable techniques were found. If two
consecutive queries yield no new techniques beyond what earlier queries found,
skip remaining queries and note skipped queries in the change report.
```

#### 4. Add Baseline Re-validation Guidance (Impact: Low)
The skill only adds/updates/removes based on new findings but doesn't re-verify existing entries.

**Current:**
```
For each section (Prompt Engineering, Context Engineering, Tool Design):
- Add new techniques not already covered
- Update existing techniques if newer evidence contradicts or supplements them
```

**Recommended:**
```
For each section (Prompt Engineering, Context Engineering, Tool Design):
- Add new techniques not already covered
- Update existing techniques if newer evidence contradicts or supplements them
- Spot-check 2-3 existing techniques per section against current sources to
  verify they remain accurate and well-evidenced
```

#### Reference File Recommendation
No additional reference files needed.

---

## Summary

| Item | Type | Overall | Clarity | Completeness | PE | CE | Goal | Safety | Meta |
|------|------|---------|---------|--------------|----|----|------|--------|------|
| review-claude-config | Skill | **A** | A | A | A | A | A | B | A |
| refresh-engineering-baseline | Skill | **A** | A | A | A | B | A | A | B |

## Cross-Cutting Observations

**Common anti-patterns:**
- Both skills list tools in `allowed-tools` that are not actually used in their workflows (Grep in review-claude-config, Glob in refresh-engineering-baseline). Consistent tool set curation issue.

**Consistent strengths:**
- Both skills demonstrate strong safety design with confirmation gates before writes and explicit stop conditions.
- Both use effective prompt engineering with role priming, structured output templates, and explicit constraints.
- Both follow conservative defaults — when anything fails, the system preserves existing state.

**Systemic recommendations:**
- Audit all `allowed-tools` declarations against actual tool usage in the skill body. Remove any tool not referenced in the workflow.
- Both skills would benefit from grading boundary examples (review-claude-config) or frontmatter robustness checks (refresh-engineering-baseline) to handle edge cases more deterministically.
