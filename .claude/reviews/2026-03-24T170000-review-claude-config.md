---
generated_by: review-claude-config
schema_version: 1
date: 2026-03-24
target: /Users/ntbc/workspace/claude/review-claude-config
baseline_version: 2026-03-24
items_reviewed: 8
summary:
  - name: review-claude-config
    type: Skill
    path: .claude/skills/review-claude-config/SKILL.md
    overall: A
    score: 95.0
    clarity: A
    completeness: A
    prompt_engineering: A
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
  - name: suggest-skills
    type: Skill
    path: .claude/skills/suggest-skills/SKILL.md
    overall: A
    score: 90.8
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
    overall: A
    score: 93.0
    clarity: A
    completeness: A
    prompt_engineering: A
    context_engineering: B
    goal_alignment: A
    safety: A
    metadata: B
  - name: apply-review-findings
    type: Skill
    path: .claude/skills/apply-review-findings/SKILL.md
    overall: A
    score: 93.5
    clarity: A
    completeness: A
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
  - name: skill-scaffolding
    type: Skill
    path: .claude/skills/skill-scaffolding/SKILL.md
    overall: A
    score: 92.0
    clarity: A
    completeness: B
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
  - name: check-repo-health
    type: Skill
    path: .claude/skills/check-repo-health/SKILL.md
    overall: A
    score: 92.0
    clarity: A
    completeness: B
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
  - name: review-analytics
    type: Skill
    path: .claude/skills/review-analytics/SKILL.md
    overall: A
    score: 91.2
    clarity: A
    completeness: B
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
  - name: research-index
    type: Skill
    path: .claude/skills/research-index/SKILL.md
    overall: A
    score: 91.3
    clarity: A
    completeness: B
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
---

# Review Report — 2026-03-24T170000

## Item 1: review-claude-config

**Type:** Skill | **Path:** `.claude/skills/review-claude-config/SKILL.md`

### Goal
Orchestrate a comprehensive, evidence-based quality audit of all Claude Code skills and agents in a project directory, scoring each against a 7-dimension rubric and producing traceable review reports with concrete improvement recommendations.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Explicit 4-phase sequential workflow with numbered steps, deterministic conditionals (CACHED/STALE/MISS with researcher/consumer roles), unambiguous parallel/sequential boundaries |
| Completeness | A | 15% | Edge cases handled (no `.claude/`, no items, WebSearch/WebFetch unavailable, agent failure, >20 items, missing INDEX.md), output format fully defined |
| Prompt Engineering | A | 15% | Structured output templates (certificate table), role priming, chain-of-thought, few-shot grading boundary examples, constraint specification, verification criteria (worked example) |
| Context Engineering | A | 15% | Subagent isolation, JIT domain cache retrieval, KV-cache byte-identical prefix, reference file separation, batched dispatch (groups of 8), progressive disclosure |
| Goal Alignment | A | 20% | Domain cache for persistent knowledge, multi-dimensional rubric, concrete rewrites, delta comparison, cross-cutting observations, audit-to-fix traceability |
| Safety | A | 15% | Read-only hard rule, confirmation gates before writing reports and cache, analysis agents scoped to WebSearch+WebFetch+Read only, error handling without silent skipping |
| Metadata | A | 5% | Complete frontmatter, description accurately matches body, tool list matches actual usage |
| **Overall** | **A** | **100%** | **Weighted: 95.0 → A** |

### Strengths
- Sophisticated domain cache system with researcher/consumer roles prevents redundant web searches
- Exemplary context engineering with KV-cache optimization and batched parallel execution
- Complete traceability chain: YAML frontmatter, delta comparison, timestamp-linked commits

### Recommendations

#### 1. Specify WebFetch timeout/failure handling in analysis agents (Impact: Low)
Analysis agents are told to fetch URLs but have no guidance on handling individual fetch failures mid-analysis.

**Current:**
```
After WebSearch returns results, identify the 1-2 most relevant URLs
(prefer primary sources: official docs, peer-reviewed papers, production
case studies). Fetch each with WebFetch using a targeted prompt:
```

**Recommended:**
```
After WebSearch returns results, identify the 1-2 most relevant URLs
(prefer primary sources: official docs, peer-reviewed papers, production
case studies). Fetch each with WebFetch using a targeted prompt:
"Extract domain best practices, benchmarks, and configuration patterns
relevant to [domain]. Max 500 words."
If a WebFetch call fails or returns empty content, proceed with WebSearch
snippets for that URL — do not retry or block on fetch failures.
```

#### 2. Add batch-level failure escalation (Impact: Low)
Individual agent failure is handled but entire-batch failure has no escalation guidance.

**Current:**
```
- **Error handling:** If an analysis agent fails, report the failure with partial results and continue with remaining items. Never silently skip.
```

**Recommended:**
```
- **Error handling:** If an analysis agent fails, report the failure with partial results and continue with remaining items. Never silently skip. If all agents in a batch fail, report the systemic error before proceeding. If two consecutive batches fail completely, stop and report.
```

---

## Item 2: suggest-skills

**Type:** Skill | **Path:** `.claude/skills/suggest-skills/SKILL.md`

### Goal
Identify missing Claude Code skills in a repository through systematic signal detection and open reasoning, outputting a prioritized suggestion report with skeleton SKILL.md files.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Explicit 4-phase workflow with numbered steps, parallel execution points clearly marked, deterministic sequencing |
| Completeness | A | 15% | Edge cases: empty folder, scan agent failure, partial Phase 2 failure, tool unavailability, >60% overlap, >10 suggestions cap, minimum-3 rule |
| Prompt Engineering | A | 15% | Role priming, structured output templates, constraint specification, chain-of-thought (Layer 2 with 4 gap categories), output format templates |
| Context Engineering | A | 15% | Reference separation (signal-catalog.md), subagent isolation (scan/Layer 1/Layer 2 each with minimal tools), JIT domain cache lookup, KV-cache design |
| Goal Alignment | A | 20% | Hybrid Layer 1/Layer 2 approach, extraction criteria as false-positive gate, repository type classification, coverage map deduplication |
| Safety | A | 10% | Read-only on target (hard rule), write limited to report file, confirmation gate, graceful degradation |
| Metadata | B | 10% | Complete frontmatter. Write in allowed-tools for report output not clarified in description; missing `disable-model-invocation: true` |
| **Overall** | **A** | **100%** | **Weighted: 90.8 → A** |

### Strengths
- Research-grounded hybrid architecture (static table matching + open reasoning)
- Excellent subagent isolation with precisely scoped tools per agent
- Repository type awareness (Application/Skills-Config/Mixed) with distinct signal tables

### Recommendations

#### 1. Add report output mention to description (Impact: Medium)

**Current:**
```yaml
description: >
  Analyze a repository's structure, workflows, and documentation to identify
  missing Claude Code skills. Produces a prioritized report with rationale and
  skeleton SKILL.md for each suggestion. Use when setting up Claude Code in a
  new project or expanding skill coverage in an existing one.
```

**Recommended:**
```yaml
description: >
  Analyze a repository's structure, workflows, and documentation to identify
  missing Claude Code skills. Produces a prioritized report with rationale and
  skeleton SKILL.md for each suggestion, saved to <target>/.claude/reviews/.
  Use when setting up Claude Code in a new project or expanding skill coverage
  in an existing one.
```

#### 2. Remove unnecessary Read tool from Layer 1 agent (Impact: Medium)
Layer 1 agent has all inputs inlined in the prompt; Read is never used.

**Current:**
```
Allowed-tools: Read only (no web research needed for table matching).
```

**Recommended:**
```
Allowed-tools: none (all inputs are inlined in the prompt — no file reads needed).
```

#### 3. Add `disable-model-invocation: true` (Impact: Low)
Consistent with project convention for skills that write files.

**Current:**
```yaml
allowed-tools: Agent, Read, Write, Glob, Grep, WebSearch, WebFetch
```

**Recommended:**
```yaml
allowed-tools: Agent, Read, Write, Glob, Grep, WebSearch, WebFetch
disable-model-invocation: true
```

---

## Item 3: refresh-engineering-baseline

**Type:** Skill | **Path:** `.claude/skills/refresh-engineering-baseline/SKILL.md`

### Goal
Maintain the engineering baseline reference file by refreshing it with current, evidence-based prompt/context/tool-design techniques sourced from web research, enforcing source quality, preserving structure, respecting token budgets, and requiring user confirmation.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Seven sequential steps with explicit conditions, decision points, and failure paths |
| Completeness | A | 15% | Covers WebSearch unavailability, partial results, WebFetch unavailability, zero results, token budget overflow, user decline |
| Prompt Engineering | A | 15% | Role priming ("research librarian"), structured report template, constraint specification, merge decision example, verification criteria |
| Context Engineering | B | 15% | Good structure but hardcoded baseline path reduces portability; no subagent isolation for research queries |
| Goal Alignment | A | 20% | Source quality criteria (credible, actionable, cross-validated) are well-calibrated; 18-month cutoff prevents stale sources |
| Safety | A | 15% | `disable-model-invocation: true`, confirmation gates at steps 2 and 5, hard rule against modifying if WebSearch fails |
| Metadata | B | 5% | Complete frontmatter, accurate. Minor: no `argument-hint` field (acceptable since skill takes no arguments) |
| **Overall** | **A** | **100%** | **Weighted: 93.0 → A** |

### Strengths
- Excellent failure handling with distinct responses for each failure mode
- Strong source quality criteria with three-part filter (credible, actionable, cross-validated)
- Clear merge decision example eliminates common ambiguity
- Token budget enforcement with prioritized removal strategy

### Recommendations

#### 1. Add spot-check results to report template (Impact: Medium)
Step 4 instructs spot-checking 2-3 existing techniques but the report template has no output slot, making it unverifiable.

**Current:**
```markdown
### Removed
- **[Technique Name]** — Reason: [why removed]. Evidence: [source]
```

**Recommended:**
```markdown
### Removed
- **[Technique Name]** — Reason: [why removed]. Evidence: [source]

### Spot-Checked (No Change Needed)
- **[Technique Name]** — Verified against: [source]. Still accurate.
```

#### 2. Clarify "no new techniques" deduplication threshold (Impact: Low)

**Current:**
```markdown
After each query, check if new actionable techniques were found. If two consecutive queries yield no new techniques beyond what earlier queries found, skip remaining queries
```

**Recommended:**
```markdown
After each query, check if new actionable techniques were found. A technique is "new" only if it is not semantically equivalent to any technique already extracted (same core practice, different wording does not count). If two consecutive queries yield no new techniques, skip remaining queries
```

---

## Item 4: apply-review-findings

**Type:** Skill | **Path:** `.claude/skills/apply-review-findings/SKILL.md`

### Goal
Apply structured review recommendations from `/review-claude-config` reports to reviewed files, maintaining audit-fix traceability through scoped conventional commits with user confirmation at every step.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Seven sequential phases with explicit substeps, decision points (yes/no/skip/stop) are unambiguous, edge case recovery flows |
| Completeness | A | 15% | Covers: report discovery, validation, parsing, impact filtering, per-edit confirmation, commit ordering, text-not-found recovery, uncommitted reports |
| Prompt Engineering | B | 15% | Role priming, structured output tables, constraints in Hard Rules. Missing: few-shot example of recommendation parsing |
| Context Engineering | A | 15% | JIT reference loading (commit-conventions.md at step 6), minimal tool set (Read, Edit, Glob, Bash), self-contained parsing |
| Goal Alignment | A | 20% | Audit-fix chain matches CLAUDE.md conventions exactly, High/Medium filtering aligns with prioritized remediation, re-review suggestion closes feedback loop |
| Safety | A | 15% | `disable-model-invocation: true`, three-level confirmation (start, each edit, commit), edit-only constraint, scope restriction to report-listed files |
| Metadata | A | 5% | Complete frontmatter with name, description, argument-hint, allowed-tools, disable-model-invocation |
| **Overall** | **A** | **100%** | **Weighted: 93.5 → A** |

### Strengths
- Layered confirmation gates (summary approval, per-edit with skip/stop, commit approval)
- Robust "text not found" recovery flow for files changed since review
- Timestamp-linked commit chain creates verifiable audit trail

### Recommendations

#### 1. Add few-shot example of recommendation parsing (Impact: Medium)
The parsing pattern shows structure but doesn't demonstrate handling variations (e.g., recommendations without code blocks).

**Current:**
```markdown
Parse the report body for recommendation sections. Each recommendation follows this pattern:
```

**Recommended:**
```markdown
Parse the report body for recommendation sections. Each recommendation follows this pattern:
[... existing pattern ...]

Example extraction:
- title="Add explicit error handling", impact="High", current_text=`Run WebSearch...`, recommended_text=`Run WebSearch for each topic. If WebSearch...`
- Some recommendations may lack code blocks (structural suggestions). Skip these and include them in the "not applied" summary.
```

#### 2. Specify behavior for multi-file recommendations (Impact: Medium)
A single recommendation may affect multiple files. Current workflow assumes one-to-one mapping.

**Current:**
```markdown
1. Read the target file at the path from the report's `summary` section.
```

**Recommended:**
```markdown
1. Identify the target file(s). If the recommendation references multiple files or uses "all skills", collect affected paths from the summary.
2. For each target file, follow the same preview→confirm→edit flow.
```

---

## Item 5: skill-scaffolding

**Type:** Skill | **Path:** `.claude/skills/skill-scaffolding/SKILL.md`

### Goal
Automate creation of new Claude Code skill directories with valid SKILL.md files, reference file stubs, and CLAUDE.md registration, following project conventions and the skill format specification.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Seven numbered steps with explicit inputs, outputs, and decision points; validation-first pattern prevents wasted work |
| Completeness | B | 15% | Core cases covered well. Missing: error handling for CLAUDE.md registration failures, no post-write verification step |
| Prompt Engineering | B | 15% | Role priming, constraint specification (Hard Rules), output format for commit message. Missing: explicit output template for generated SKILL.md |
| Context Engineering | A | 15% | JIT loading (template + optional conventions research via Glob), minimal tool set (Read, Write, Edit, Glob), graceful fallback |
| Goal Alignment | A | 20% | Complete scaffolding pipeline covering frontmatter, body, references, and registration; conventions-aware |
| Safety | A | 15% | `disable-model-invocation: true`, preview-before-write loop (yes/edit/cancel), duplicate detection, additive-only CLAUDE.md edits |
| Metadata | A | 5% | Complete frontmatter with all fields accurately matching body |
| **Overall** | **A** | **100%** | **Weighted: 92.0 → A** |

### Strengths
- Preview-before-write loop (yes/edit/cancel) is textbook safety for write-capable skills
- Complete CLAUDE.md registration covering all three sections with additive-only constraint
- JIT context loading with graceful fallback when conventions file is absent

### Recommendations

#### 1. Add output format template for generated SKILL.md (Impact: Medium)
The skill says "build from template" but doesn't specify the exact output structure, leaving interpretation room.

**Current:**
```markdown
### 4. Generate SKILL.md
Build the SKILL.md content from the template:
- **Frontmatter:** Fill in fields based on user answers.
- **Role statement:** Generate a one-sentence role description.
- **Workflow section:** Generate numbered step stubs.
- **Hard Rules section:** Include standard rules.
```

**Recommended:**
```markdown
### 4. Generate SKILL.md
Build the SKILL.md content from the template. The generated file MUST follow this structure:

\`\`\`
---
name: <skill-name>
description: >
  <user-provided description>
argument-hint: "<hint>"    # omit if none
allowed-tools: <tools>
disable-model-invocation: true  # omit if read-only
---

# <Skill Title>

<Role statement: "You are a [role] that [purpose]. Your job is to [core task].">

## Workflow
### 1. <Step name>
<1-2 sentence description>

## Hard Rules
- <constraints>
\`\`\`
```

#### 2. Add error handling for CLAUDE.md registration (Impact: Medium)
If CLAUDE.md is missing or lacks expected sections, Edit calls fail silently.

**Current:**
```markdown
Read CLAUDE.md. Add entries to three sections:
```

**Recommended:**
```markdown
Read CLAUDE.md from the repository root. If CLAUDE.md is missing, tell the user: "No CLAUDE.md found. Skill directory was created but not registered."
If a section heading is not found, skip it and warn: "Could not find '## <section>' in CLAUDE.md. Add the entry manually."
```

---

## Item 6: check-repo-health

**Type:** Skill | **Path:** `.claude/skills/check-repo-health/SKILL.md`

### Goal
Monitor a skills repository for three maintenance dimensions (freshness, token budgets, reference integrity) and produce a consolidated health dashboard with PASS/WARN/FAIL status and remediation guidance.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Clear parse-discover-check-present pipeline with numbered steps, explicit logic per check |
| Completeness | B | 15% | Core checks thorough. Missing: handling files without `last_refreshed`, unclear whether research files get freshness checks |
| Prompt Engineering | B | 15% | Role priming, structured output template (full dashboard), constraints (Hard Rules). Missing: verification step before presenting |
| Context Engineering | A | 15% | Minimal tools (Read, Glob only), externalized thresholds via reference file, efficient INDEX.md bulk read |
| Goal Alignment | A | 20% | Three-dimensional health model covers key maintenance concerns, remediation guidance is actionable and context-specific |
| Safety | A | 10% | Read-only with explicit hard rule, graceful degradation on missing files |
| Metadata | A | 10% | Complete frontmatter, accurate description, argument-hint, tool list matches usage |
| **Overall** | **A** | **100%** | **Weighted: 92.0 → A** |

### Strengths
- Minimal, appropriate tool set (Read + Glob only) — textbook least-privilege
- Externalized thresholds via reference file for configurability
- Full dashboard template with conditional remediation section
- Graceful degradation hard rule prevents cascading failures

### Recommendations

#### 1. Specify handling of files without `last_refreshed` (Impact: Medium)

**Current:**
```markdown
For each reference file with a `last_refreshed` field in its YAML frontmatter:
1. Read the file and extract the `last_refreshed` date.
```

**Recommended:**
```markdown
For each reference file, read and check for `last_refreshed` in frontmatter:
- If present, extract date and compute days since refresh.
- If missing, record as **WARN** with note "No last_refreshed date in frontmatter."
```

#### 2. Clarify research file scope for freshness checks (Impact: Medium)

**Current:**
```markdown
### 3. Check freshness (if `all` or `freshness`)
For each reference file with a `last_refreshed` field...
```

**Recommended:**
```markdown
### 3. Check freshness (if `all` or `freshness`)
Check freshness only for files under `.claude/skills/*/references/` (including domain cache). Research files (`research/**/*.md`) are checked only in the integrity step, not for freshness.
```

#### 3. Add result verification before presenting (Impact: Low)

**Current:**
```markdown
### 6. Present dashboard
```

**Recommended:**
```markdown
### 6. Verify results
Before presenting, verify: every file in freshness also appears in tokens (if both ran), no duplicate rows, all FAIL entries have remediation.

### 7. Present dashboard
```

---

## Item 7: review-analytics

**Type:** Skill | **Path:** `.claude/skills/review-analytics/SKILL.md`

### Goal
Parse accumulated review reports, compute grade trajectories per item and dimension, detect regressions, and present a portfolio health dashboard showing quality evolution over time.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Sequential numbered workflow, explicit table formats, unambiguous trajectory classification rules |
| Completeness | B | 15% | Core cases well covered (single-report, new/removed items, malformed reports). Missing: non-monotonic trajectory handling, duplicate item names |
| Prompt Engineering | B | 15% | Role priming ("quality analyst"), structured output templates (3 views), constraints, explicit grade comparison order. Missing: few-shot example |
| Context Engineering | A | 15% | Minimal tools (Read, Glob only), JIT reference loading (report-schema.md at step 2) |
| Goal Alignment | A | 20% | Directly serves "iterate until convergence" workflow, trajectory+regression detection, systemic issue detection adds analytical value |
| Safety | A | 10% | Read-only with explicit hard rule, graceful degradation on malformed input |
| Metadata | A | 10% | Complete and accurate frontmatter |
| **Overall** | **A** | **100%** | **Weighted: 91.2 → A** |

### Strengths
- Three distinct output views (trajectories, heatmap, alerts) provide comprehensive quality picture
- Robust edge case handling for zero/one reports, malformed frontmatter, new/removed items
- Minimal attack surface with Read + Glob only

### Recommendations

#### 1. Add non-monotonic trajectory handling (Impact: Medium)
Current classification has a gap: A→C→B could match both criteria ambiguously.

**Current:**
```markdown
- **Improving** — Latest grade is higher than the earliest, OR score increased by ≥5 points.
- **Stable** — Grade unchanged across all reports, AND score variation < 5 points.
- **Regressing** — Latest grade is lower than the previous report, OR score dropped by ≥5 points.
```

**Recommended:**
```markdown
- **Regressing** — Latest grade is lower than the previous report, OR score dropped by ≥5 points vs previous. (Evaluated first — regression takes priority.)
- **Improving** — Latest grade is higher than the earliest, OR score increased by ≥5 points vs earliest. (Evaluated second.)
- **Stable** — Grade unchanged across all reports, AND score variation < 5 points. (Default.)
- **Mixed** — Does not fit above categories (e.g., non-monotonic: A → C → B). Show trajectory arrows.
```

#### 2. Add duplicate item name handling (Impact: Low)

**Current:**
```markdown
- **Read-only.** Never modify any file.
```

**Recommended:**
```markdown
- **Read-only.** Never modify any file.
- **Duplicate item names.** If a report contains duplicate item names, use the last occurrence and warn.
```

---

## Item 8: research-index

**Type:** Skill | **Path:** `.claude/skills/research-index/SKILL.md`

### Goal
Detect drift between on-disk `research/` files and the CLAUDE.md Research References section, report discrepancies, and optionally sync CLAUDE.md to match reality.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Numbered sequential steps, clear stop conditions at each phase, explicit format examples |
| Completeness | B | 15% | Core and edge cases covered (missing directory, no section, all-OK). Missing: malformed entry handling, Edit failure recovery |
| Prompt Engineering | B | 15% | Role priming ("index maintainer"), structured output template, constraints. Missing: CoT guidance, few-shot for ambiguous cases |
| Context Engineering | A | 15% | Minimal tools (Read, Edit, Glob), JIT retrieval (first 5 lines for title), Edit scoped to one section |
| Goal Alignment | A | 20% | Serves project's "every claim needs a source" convention, follows commit format, matches CLAUDE.md constraint |
| Safety | A | 15% | `disable-model-invocation: true`, hard rule restricting edits to one section, user confirmation gate |
| Metadata | A | 5% | Complete frontmatter, all fields accurate |
| **Overall** | **A** | **100%** | **Weighted: 91.3 → A** |

### Strengths
- Precise tool scoping (Read, Edit, Glob only) — minimum needed
- Clear stop conditions at each phase prevent undefined states
- Strong safety model with dual-layer protection (`disable-model-invocation` + confirmation gate)

### Recommendations

#### 1. Add malformed entry handling (Impact: Medium)

**Current:**
```markdown
Parse each entry in the section. Expected format:
- [Title](relative/path) — Description

Extract for each entry: title, relative path, description.
```

**Recommended:**
```markdown
Parse each entry in the section. Expected format:
- [Title](relative/path) — Description

Extract for each entry: title, relative path, description.

If an entry does not match the expected format, classify as **MALFORMED** in the report. Do not modify malformed entries during sync — preserve as-is and warn.
```

#### 2. Add title-mismatch detection (Impact: Low)
Description mentions "description mismatches" but Step 3 only classifies OK/UNLINKED/BROKEN — never compares titles.

**Current:**
```markdown
- **OK** — File exists on disk AND is referenced in CLAUDE.md.
- **UNLINKED** — File exists on disk but is NOT referenced in CLAUDE.md.
- **BROKEN** — Referenced in CLAUDE.md but file does NOT exist on disk.
```

**Recommended:**
```markdown
- **OK** — File exists on disk AND is referenced in CLAUDE.md.
- **UNLINKED** — File exists on disk but is NOT referenced in CLAUDE.md.
- **BROKEN** — Referenced in CLAUDE.md but file does NOT exist on disk.
- **STALE** — File exists and is linked, but the title differs from the `#` heading on disk.
```

#### 3. Add Edit failure recovery guidance (Impact: Low)

**Current:**
```markdown
Use Edit to make targeted changes to the `## Research References` section only.
```

**Recommended:**
```markdown
Use Edit to make targeted changes to the `## Research References` section only.
Apply all additions first, then all removals. If any Edit fails, stop, show which changes succeeded/failed, and suggest re-running.
```

---

## Summary

| Item | Type | Overall | Clarity | Completeness | PE | CE | Goal | Safety | Meta |
|------|------|---------|---------|--------------|----|----|------|--------|------|
| review-claude-config | Skill | **A** (95.0) | A | A | A | A | A | A | A |
| suggest-skills | Skill | **A** (90.8) | A | A | A | A | A | A | B |
| refresh-engineering-baseline | Skill | **A** (93.0) | A | A | A | B | A | A | B |
| apply-review-findings | Skill | **A** (93.5) | A | A | B | A | A | A | A |
| skill-scaffolding | Skill | **A** (92.0) | A | B | B | A | A | A | A |
| check-repo-health | Skill | **A** (92.0) | A | B | B | A | A | A | A |
| review-analytics | Skill | **A** (91.2) | A | B | B | A | A | A | A |
| research-index | Skill | **A** (91.3) | A | B | B | A | A | A | A |

## Cross-Cutting Observations

### Consistent Strengths
- **Clarity is universally A.** All 8 skills have explicit sequential workflows with numbered steps and deterministic behavior.
- **Safety is universally A.** Every write-capable skill has `disable-model-invocation: true` and confirmation gates. Read-only skills use least-privilege tool sets.
- **Context engineering is strong across the board.** JIT retrieval, reference file separation, and minimal tool sets are consistent patterns.

### Common Patterns
- **Prompt Engineering B pattern (5/8 items).** The 5 items scoring B in PE share the same gap: missing few-shot examples. All use role priming, structured output, and constraints, but none provide concrete input→output examples for non-obvious decision points.
- **Completeness B pattern (4/8 items).** The 4 items scoring B in Completeness share a pattern of missing error handling for malformed inputs or tool failure edge cases (CLAUDE.md missing sections, Edit failures, malformed report entries).

### Systemic Recommendations
1. **Add few-shot examples to all skills scoring PE=B.** Each skill has at least one non-obvious decision point that would benefit from a concrete example.
2. **Standardize error recovery patterns.** Create a shared reference with error handling templates for common failure modes (Edit failures, missing files, malformed inputs).

## Delta from Prior Review (2026-03-24T161200)

| Item | Dimension | Previous | Current | Change |
|------|-----------|----------|---------|--------|
| review-claude-config | Safety | B | A | +1 |
| review-claude-config | Overall Score | 93.5 | 95.0 | +1.5 |
| suggest-skills | — | — | A (90.8) | New |
| apply-review-findings | — | — | A (93.5) | New |
| skill-scaffolding | — | — | A (92.0) | New |
| check-repo-health | — | — | A (92.0) | New |
| review-analytics | — | — | A (91.2) | New |
| research-index | — | — | A (91.3) | New |

Note: Prior review only covered 2 items (review-claude-config, refresh-engineering-baseline). This is the first full-portfolio review of all 8 skills. refresh-engineering-baseline maintained its A grade (93.0 → 93.0, stable).
