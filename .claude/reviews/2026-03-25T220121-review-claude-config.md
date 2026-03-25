---
generated_by: review-claude-config
schema_version: 1
date: 2026-03-25
target: /Users/ntbc/workspace/claude/review-claude-config
baseline_version: 2026-03-24
items_reviewed: 14
summary:
  - name: review-agent
    type: Skill
    path: skills/review-agent/SKILL.md
    overall: A
    score: 95.0
    clarity: A
    completeness: A
    prompt_engineering: A
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
  - name: review-rule
    type: Skill
    path: skills/review-rule/SKILL.md
    overall: A
    score: 95.0
    clarity: A
    completeness: A
    prompt_engineering: A
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
  - name: review-skill
    type: Skill
    path: skills/review-skill/SKILL.md
    overall: A
    score: 93.5
    clarity: A
    completeness: A
    prompt_engineering: A
    context_engineering: A
    goal_alignment: A
    safety: B
    metadata: A
  - name: review-claude-config
    type: Skill
    path: skills/review-claude-config/SKILL.md
    overall: A
    score: 92.0
    clarity: A
    completeness: A
    prompt_engineering: A
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: B
  - name: review-analytics
    type: Skill
    path: .claude/skills/review-analytics/SKILL.md
    overall: A
    score: 91.0
    clarity: A
    completeness: A
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
  - name: refresh-engineering-baseline
    type: Skill
    path: .claude/skills/refresh-engineering-baseline/SKILL.md
    overall: A
    score: 91.0
    clarity: A
    completeness: A
    prompt_engineering: A
    context_engineering: B
    goal_alignment: A
    safety: A
    metadata: B
  - name: suggest-skills
    type: Skill
    path: skills/suggest-skills/SKILL.md
    overall: A
    score: 91.0
    clarity: A
    completeness: A
    prompt_engineering: A
    context_engineering: A
    goal_alignment: A
    safety: B
    metadata: A
  - name: apply-rule-review-findings
    type: Skill
    path: skills/apply-rule-review-findings/SKILL.md
    overall: A
    score: 90.6
    clarity: A
    completeness: A
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
  - name: apply-skill-review-findings
    type: Skill
    path: skills/apply-skill-review-findings/SKILL.md
    overall: A
    score: 90.5
    clarity: A
    completeness: A
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
  - name: check-repo-health
    type: Skill
    path: .claude/skills/check-repo-health/SKILL.md
    overall: A
    score: 90.4
    clarity: A
    completeness: A
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: A
  - name: apply-review-findings
    type: Skill
    path: skills/apply-review-findings/SKILL.md
    overall: A
    score: 89.8
    clarity: A
    completeness: A
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: B
  - name: apply-agent-review-findings
    type: Skill
    path: skills/apply-agent-review-findings/SKILL.md
    overall: B
    score: 89.6
    clarity: A
    completeness: A
    prompt_engineering: B
    context_engineering: B
    goal_alignment: A
    safety: A
    metadata: A
  - name: skill-scaffolding
    type: Skill
    path: .claude/skills/skill-scaffolding/SKILL.md
    overall: B
    score: 88.7
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
    overall: B
    score: 87.6
    clarity: A
    completeness: B
    prompt_engineering: B
    context_engineering: A
    goal_alignment: B
    safety: A
    metadata: B
---

# Review Report — 2026-03-25T220121

## Item 1: review-claude-config (Plugin — Orchestrator)

**Type:** Skill | **Path:** `skills/review-claude-config/SKILL.md`

### Goal
Analyze all Claude Code skills, agents, and rules in a project and produce per-item quality certificates with optimization recommendations.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Explicit phased workflow with parallel/sequential markers, deterministic conditionals |
| Completeness | A | 15% | Covers discovery, analysis, cache, reporting, delta comparison, large codebase handling, error handling |
| Prompt Engineering | A | 15% | Structured output templates, chain-of-thought, constraint specification, output format templates |
| Context Engineering | A | 15% | Exemplary KV-cache optimization, reference separation, JIT retrieval, subagent isolation, batched dispatch |
| Goal Alignment | A | 20% | Delegates to specialized reviewers, domain cache enriches analysis, delta comparison enables convergence |
| Safety | A | 15% | Read-only on analyzed files, confirmation gates, analysis agents denied destructive tools |
| Metadata | B | 5% | Description says "optimize" but skill is read-only (recommends, doesn't apply) |
| **Overall** | **A** | **100%** | **Weighted: 92.0** |

### Strengths
- KV-cache-friendly dispatch with byte-identical shared prefixes per type group
- Domain cache CACHED/STALE/MISS protocol eliminates redundant web queries
- Delta comparison with prior reports supports iterative convergence

### Recommendations

#### 1. Change "optimize" to "evaluate" in description (Impact: Medium)

**Current:**
```yaml
description: >
  Analyze and optimize all Claude Code skills, agents, and rules in a project's
  .claude/ directory.
```

**Recommended:**
```yaml
description: >
  Analyze and evaluate all Claude Code skills, agents, and rules in a project's
  .claude/ directory.
```

#### 2. Pin WebSearch connectivity check query (Impact: Low)

**Current:**
```
Attempt a trivial WebSearch (e.g., "Claude Code documentation").
```

**Recommended:**
```
Attempt WebSearch with query "Claude Code documentation" as a connectivity check.
```

---

## Item 2: review-skill (Plugin)

**Type:** Skill | **Path:** `skills/review-skill/SKILL.md`

### Goal
Evaluate a single SKILL.md across 7 dimensions with a quality certificate.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Explicit phased workflow, clear mode detection |
| Completeness | A | 15% | Handles orchestrated/standalone, validation, error handling, output fully specified |
| Prompt Engineering | A | 15% | Structured output, boundary examples as calibration, grade calculation formula |
| Context Engineering | A | 15% | Progressive disclosure, JIT reference loading, mode-based phase skipping |
| Goal Alignment | A | 20% | Directly maps to evaluation goal, domain research enriches, concrete rewrite requirement |
| Safety | B | 15% | Read-only, confirmation gate; no explicit WebFetch retry bound |
| Metadata | A | 5% | Complete, accurate, tool list matches usage |
| **Overall** | **A** | **100%** | **Weighted: 93.5** |

### Strengths
- Dual-mode architecture, grading boundary examples, ecosystem-enabling frontmatter schema

### Recommendations

#### 1. Add explicit WebFetch failure/retry bound (Impact: Low)

**Current:**
```
- If `webfetch_available`: fetch 1-2 most relevant URLs with WebFetch using prompt: "Extract domain best practices, benchmarks, and configuration patterns relevant to [domain]. Max 500 words."
```

**Recommended:**
```
- If `webfetch_available`: fetch up to 2 URLs with WebFetch using prompt: "Extract domain best practices, benchmarks, and configuration patterns relevant to [domain]. Max 500 words." If a fetch fails or returns irrelevant content, skip it -- do not retry.
```

---

## Item 3: review-agent (Plugin)

**Type:** Skill | **Path:** `skills/review-agent/SKILL.md`

### Goal
Evaluate a single agent across 7 dimensions with agent-specific checks.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Deterministic phases, clear branching |
| Completeness | A | 15% | Type guard, mode detection, error handling, output format specified |
| Prompt Engineering | A | 15% | Structured output, boundary examples, role priming |
| Context Engineering | A | 15% | JIT loading, type-specific guide separation, domain cache passthrough |
| Goal Alignment | A | 20% | Agent-specific criteria (activation precision, model selection, trigger coverage) |
| Safety | A | 15% | Read-only, confirmation gate, no Bash |
| Metadata | A | 5% | Complete, accurate, describes all three agent-specific checks |
| **Overall** | **A** | **100%** | **Weighted: 95.0** |

### Strengths
- Precise agent adaptations (activation precision replaces progressive disclosure in CE)
- Reference file recommendation correctly notes agents can't have references

### Recommendations

#### 1. Add heuristic for agent vs rule distinction (Impact: Low)

**Current:**
```
- If the file does not look like an agent (e.g., it's a SKILL.md or rule), report the error and stop.
```

**Recommended:**
```
- If the file does not look like an agent (e.g., it's a SKILL.md, or a rule file with no frontmatter and directive-style prose), report the error and stop. Heuristic: agents typically live in `agents/` directories and have a `description` field; rules live in `rules/` directories and lack frontmatter entirely.
```

---

## Item 4: review-rule (Plugin)

**Type:** Skill | **Path:** `skills/review-rule/SKILL.md`

### Goal
Evaluate a single rule across 3 dimensions (Clarity, Completeness, Goal Alignment).

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Deterministic workflow, mode branching, explicit stop conditions |
| Completeness | A | 15% | Type mismatch guard, edge cases, output format specified |
| Prompt Engineering | A | 15% | Structured output, rule-specific boundary examples, calculation steps |
| Context Engineering | A | 15% | JIT loading, shared references, type-specific guide |
| Goal Alignment | A | 20% | Correctly adapts 7-dim to 3-dim with renormalized weights |
| Safety | A | 15% | Read-only, confirmation gate, type mismatch guard |
| Metadata | A | 5% | Complete, accurately conveys 3-dimension scope |
| **Overall** | **A** | **100%** | **Weighted: 95.0** |

### Strengths
- Rule-specific boundary examples genuinely calibrated for the rule domain
- Structural parallel with review-skill while correctly adapted

### Recommendations

#### 1. Add guidance for rules referencing other rules (Impact: Low)

**Current:**
```
- `$ARGUMENTS` is the path to a rule .md file.
- Validate the file exists. Rules are plain Markdown files, typically in `.claude/rules/`, with no standardized frontmatter.
```

**Recommended:**
```
- `$ARGUMENTS` is the path to a rule .md file.
- Validate the file exists. Rules are plain Markdown files, typically in `.claude/rules/`, with no standardized frontmatter.
- If the rule references other rules by name or path, note these as context for the Completeness dimension (rule interactions) but evaluate only the target file.
```

---

## Item 5: suggest-skills (Plugin)

**Type:** Skill | **Path:** `skills/suggest-skills/SKILL.md`

### Goal
Analyze a repository to identify missing Claude Code skills with prioritized suggestions.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Explicit 4-phase workflow, parallel/sequential marked, measurable thresholds |
| Completeness | A | 15% | Edge cases handled, graceful degradation, output templated |
| Prompt Engineering | A | 15% | Structured output, role priming in subagents, extraction criteria as verification |
| Context Engineering | A | 15% | Subagent isolation, KV-cache prefix, domain cache reuse |
| Goal Alignment | A | 20% | Two-layer analysis, extraction criteria gate, repository type classification |
| Safety | B | 15% | Read-only, confirmation gate; **missing `disable-model-invocation: true`** |
| Metadata | A | 5% | Complete, accurate, tool list matches |
| **Overall** | **A** | **100%** | **Weighted: 91.0** |

### Strengths
- Two-layer hybrid architecture (deterministic + reasoning)
- Extraction criteria gate prevents low-quality suggestions
- Repository type classification tailors analysis

### Recommendations

#### 1. Add `disable-model-invocation: true` to frontmatter (Impact: High)

CLAUDE.md requires this for skills that modify files. This skill writes the suggestions report.

**Current:**
```yaml
---
name: suggest-skills
description: >
  Analyze a repository's structure, workflows, and documentation to identify
  missing Claude Code skills.
argument-hint: [folder]
allowed-tools: Agent, Read, Write, Glob, Grep, WebSearch, WebFetch
---
```

**Recommended:**
```yaml
---
name: suggest-skills
description: >
  Analyze a repository's structure, workflows, and documentation to identify
  missing Claude Code skills.
argument-hint: [folder]
allowed-tools: Agent, Read, Write, Glob, Grep, WebSearch, WebFetch
disable-model-invocation: true
---
```

#### 2. Add next-steps guidance (Impact: Medium)

**Current:**
```
Tell the user the report file path and suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS suggest-skills report`
```

**Recommended:**
```
Tell the user the report file path and suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS suggest-skills report`

Suggest next steps:
- "Use `/skill-scaffolding <skill-name>` to create any suggested skill"
- "Use `/review-claude-config` to audit the new skills after creation"
```

#### 3. Add scan depth/size limits for large repos (Impact: Medium)

**Recommended:** Add preamble to scan agent prompt:
```
Scan limits: read at most 50 lines per file, scan at most 3 directory
levels deep. If the repository is very large (>1000 files at top level),
focus on root-level config files and the first level of subdirectories.
```

---

## Item 6: apply-review-findings (Plugin — Orchestrator)

**Type:** Skill | **Path:** `skills/apply-review-findings/SKILL.md`

### Goal
Orchestrate application of review recommendations by delegating to specialized appliers.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Sequential 8-step workflow, deterministic branching |
| Completeness | A | 15% | Missing applier fallback, uncommitted report handling, no-findings exit |
| Prompt Engineering | B | 15% | Role priming, structured output; lacks concrete parsing example |
| Context Engineering | A | 15% | True thin orchestrator, JIT applier discovery, reference separation |
| Goal Alignment | A | 20% | Audit-fix chain well-implemented, sequential dispatch, re-review suggestion |
| Safety | A | 15% | `disable-model-invocation: true`, triple confirmation gates |
| Metadata | B | 5% | Accurate; could mention batch handling more prominently |
| **Overall** | **A** | **100%** | **Weighted: 89.8** |

### Strengths
- Effective delegation, audit-fix chain enforcement, graceful degradation

### Recommendations

#### 1. Add concrete recommendation parsing example (Impact: Medium)

**Current:**
```
Parse the report body for recommendation sections. Each recommendation follows this pattern:
```

**Recommended:**
```
Parse the report body for recommendation sections. Each recommendation follows this pattern:
...existing pattern...

Example extraction: Given heading "#### 2. Add confirmation gate (Impact: High)" with Current/Recommended blocks, extract: title="Add confirmation gate", impact=High, item=<from nearest ## heading or frontmatter>.
Some recommendations may lack Current/Recommended blocks (structural suggestions). Pass the full description to the applier.
```

#### 2. Add git command failure handling (Impact: Medium)

**Current:**
```
If yes, stage the modified files and commit via Bash.
```

**Recommended:**
```
If yes, stage the modified files and commit via Bash. If the commit fails (non-zero exit), show the error and tell the user: "Commit failed. Changes are applied but uncommitted. Resolve the issue and commit manually."
```

---

## Item 7: apply-skill-review-findings (Plugin)

**Type:** Skill | **Path:** `skills/apply-skill-review-findings/SKILL.md`

### Goal
Apply review recommendations to skills with skill-specific validation.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Sequential phases, measurable criteria (500 lines, token counts) |
| Completeness | A | 15% | Both modes, text-not-found handling, pre/post validation |
| Prompt Engineering | B | 15% | Role priming, structured output; lacks worked example |
| Context Engineering | A | 15% | JIT references, minimal tools, 175 lines |
| Goal Alignment | A | 20% | Skill-specific validations (line budget, inline reference, frontmatter, tools audit) |
| Safety | A | 15% | `disable-model-invocation`, triple gates, edit-only, scope restriction |
| Metadata | A | 5% | Complete, accurate |
| **Overall** | **A** | **100%** | **Weighted: 90.5** |

### Strengths
- Thorough pre/post-edit validation, layered safety, clean mode split

### Recommendations

#### 1. Add git command failure handling (Impact: Medium)

**Current:**
```
Check whether the review report has been committed: `git log --oneline --all -- <report-path>` via Bash. If not committed, tell the user:
```

**Recommended:**
```
Check whether the review report has been committed: `git log --oneline --all -- <report-path>` via Bash. If the command fails (not a git repo, or other error), warn the user and skip the commit workflow -- edits are already applied. If not committed, tell the user:
```

#### 2. Add worked example for edit cycle (Impact: Medium)

**Recommended:** Add before Phase 3 step 1:
```
Example flow: Read `skills/review-skill/SKILL.md` -> search for Current text -> found at line 45 -> pre-edit: 128 lines (under 500) -> show preview -> user says "yes" -> Edit applied -> post-edit: frontmatter valid, 128 lines OK.
```

---

## Item 8: apply-agent-review-findings (Plugin)

**Type:** Skill | **Path:** `skills/apply-agent-review-findings/SKILL.md`

### Goal
Apply review recommendations to agents with agent-specific validation.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Clear phases; minor code block nesting issue in mode detection |
| Completeness | A | 15% | Full workflow, validation, error handling |
| Prompt Engineering | B | 15% | Persona, structured output; lacks negative example |
| Context Engineering | B | 15% | JIT references; doesn't load agent format spec for validation |
| Goal Alignment | A | 20% | Single-file constraint, model complexity, trigger keywords, tools check |
| Safety | A | 15% | `disable-model-invocation`, triple gates, single-file enforcement |
| Metadata | A | 5% | Complete, accurate |
| **Overall** | **B** | **100%** | **Weighted: 89.6** |

### Strengths
- Agent-specific validations, single-file constraint enforcement, safety depth

### Recommendations

#### 1. Fix code block nesting in mode detection (Impact: Medium)

The orchestration metadata example has nested triple-backtick issues. Use tildes (`~~~`) for the outer fence or 4-space indent to avoid nesting ambiguity.

#### 2. Add report path fallback for missing `summary` field (Impact: Medium)

**Current:**
```
1. Read the target agent file at the path from the report's `summary` section.
```

**Recommended:**
```
1. Read the target agent file. Determine the path from:
   - The report's `summary` frontmatter field (if it contains file paths), or
   - The `**Path:**` line in the report body.
   If no valid path is found, ask the user to provide the agent file path.
```

#### 3. Add guidance for skipped recommendations (Impact: Medium)

**Current:**
```
- Recommendations not applied
- Suggest: "Run `/review-agent <path>` again to verify improvements."
```

**Recommended:**
```
- Recommendations not applied (with skip reason for each)
- For validation-blocked recommendations: suggest manual resolution approach
- Suggest: "Run `/review-agent <path>` again to verify improvements."
```

---

## Item 9: apply-rule-review-findings (Plugin)

**Type:** Skill | **Path:** `skills/apply-rule-review-findings/SKILL.md`

### Goal
Apply review recommendations to rules with rule-specific validation.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Sequential phases, measurable criteria |
| Completeness | A | 15% | Both modes, validation, error handling |
| Prompt Engineering | B | 15% | Persona, structured output; lacks worked example |
| Context Engineering | A | 15% | JIT references, minimal tools, 175 lines |
| Goal Alignment | A | 20% | Rule-specific: frontmatter block, weak verbs, scope qualifiers, contradiction scan |
| Safety | A | 15% | `disable-model-invocation`, triple gates, no frontmatter injection rule |
| Metadata | A | 5% | Complete, accurate |
| **Overall** | **A** | **100%** | **Weighted: 90.6** |

### Strengths
- Rule-specific validation (frontmatter block, verbs, contradiction scan), safety depth

### Recommendations

#### 1. Add worked example for edit cycle (Impact: Medium)

**Recommended:** Add a concrete example showing Current text with weak verb -> Recommended text with strong verb -> validation warning -> user approval flow.

#### 2. Fix unclosed code block in mode detection (Impact: Medium)

Same issue as apply-agent-review-findings: nested triple-backtick code blocks need tilde fencing or indentation.

---

## Item 10: skill-scaffolding (Repo-internal)

**Type:** Skill | **Path:** `.claude/skills/skill-scaffolding/SKILL.md`

### Goal
Create new skill directories with SKILL.md, references, and CLAUDE.md registration.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | 7-step sequential workflow, deterministic conditionals |
| Completeness | B | 15% | Happy path covered; missing write failure handling and rollback |
| Prompt Engineering | B | 15% | Role priming, constraints; missing few-shot example of generated output |
| Context Engineering | A | 15% | Minimal tools, JIT template loading |
| Goal Alignment | A | 20% | Correct structure, conventions, and registration |
| Safety | A | 15% | `disable-model-invocation`, confirmation gate, conflict check |
| Metadata | A | 5% | Complete, accurate |
| **Overall** | **B** | **100%** | **Weighted: 88.7** |

### Strengths
- Strong safety design, clean context management, complete registration workflow

### Recommendations

#### 1. Add write failure handling (Impact: High)

**Current:**
```
### 5. Write files

Create the skill directory and files:

1. Write `.claude/skills/<skill-name>/SKILL.md` with the generated content.
2. If reference files were specified, create `.claude/skills/<skill-name>/references/`...
```

**Recommended:**
```
### 5. Write files

Create the skill directory and files:

1. Write `.claude/skills/<skill-name>/SKILL.md` with the generated content.
2. If reference files were specified, create `.claude/skills/<skill-name>/references/`...

If any write fails, report which files were successfully created and which failed. Do not proceed to Step 6 until all files are written.
```

#### 2. Add concrete generated SKILL.md example (Impact: Medium)

Add a brief few-shot example after Step 4's instructions showing what a generated SKILL.md looks like.

---

## Item 11: review-analytics (Repo-internal)

**Type:** Skill | **Path:** `.claude/skills/review-analytics/SKILL.md`

### Goal
Parse review reports, compute grade trajectories, detect regressions, present health dashboard.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | 6-step sequential, measurable thresholds, early exits |
| Completeness | A | 15% | Edge cases: 0/1 reports, malformed frontmatter, appearing/disappearing items |
| Prompt Engineering | B | 15% | Role priming, structured output; lacks worked classification example |
| Context Engineering | A | 15% | Minimal tools (Read, Glob), JIT reference, 124 lines |
| Goal Alignment | A | 20% | Three views directly serve the goal |
| Safety | A | 10% | Read-only, graceful with malformed input |
| Metadata | A | 10% | Complete, accurate |
| **Overall** | **A** | **100%** | **Weighted: 91.0** |

### Strengths
- Excellent output specification, robust edge case handling, minimal tools

### Recommendations

#### 1. Add worked trajectory classification example (Impact: Medium)

**Current:**
```
- **Improving** — Latest grade is higher than the earliest, OR score increased by >=5 points.
- **Stable** — Grade unchanged across all reports, AND score variation < 5 points.
- **Regressing** — Latest grade is lower than the previous report, OR score dropped by >=5 points.
```

**Recommended:**
```
- **Improving** — Latest grade is higher than the earliest, OR score increased by >=5 points.
- **Stable** — Grade unchanged across all reports, AND score variation < 5 points.
- **Regressing** — Latest grade is lower than the previous report, OR score dropped by >=5 points.

Example: B(82) -> B(86) -> B(81) is Stable (grade unchanged, variation < 5). B(82) -> A(90) -> B(85) is Regressing (latest < previous).
```

---

## Item 12: research-index (Repo-internal)

**Type:** Skill | **Path:** `.claude/skills/research-index/SKILL.md`

### Goal
Detect drift between research/ files and CLAUDE.md Research References, optionally sync.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Sequential workflow, explicit stop conditions |
| Completeness | B | 15% | Description promises "description mismatches" but workflow doesn't implement it |
| Prompt Engineering | B | 15% | Role priming, structured output; lacking summary generation guidance |
| Context Engineering | A | 15% | Minimal tools, 92 lines |
| Goal Alignment | B | 20% | Core drift detection works; description mismatch detection missing |
| Safety | A | 15% | `disable-model-invocation`, confirmation gate, section-scoped editing |
| Metadata | B | 5% | Description mentions "description mismatches" not implemented |
| **Overall** | **B** | **100%** | **Weighted: 87.6** |

### Strengths
- Excellent context efficiency (92 lines, 3 tools), strong safety, clear stop conditions

### Recommendations

#### 1. Implement description mismatch detection (Impact: High)

**Current:**
```
Classify each item:
- **OK** — File exists on disk AND is referenced in CLAUDE.md.
- **UNLINKED** — File exists on disk but is NOT referenced in CLAUDE.md.
- **BROKEN** — Referenced in CLAUDE.md but file does NOT exist on disk.
```

**Recommended:**
```
Classify each item:
- **OK** — File exists on disk AND is referenced in CLAUDE.md with a matching title.
- **UNLINKED** — File exists on disk but is NOT referenced in CLAUDE.md.
- **BROKEN** — Referenced in CLAUDE.md but file does NOT exist on disk.
- **STALE** — File exists and is referenced, but the CLAUDE.md title does not match the file's heading.
```

#### 2. Add folder validation (Impact: Medium)

**Current:**
```
Glob `<target>/research/**/*.md` to find all research files.
```

**Recommended:**
```
Verify `<target>` exists using Glob on `<target>/CLAUDE.md`. If it does not exist, tell the user: "Target folder not found or has no CLAUDE.md." Stop.

Glob `<target>/research/**/*.md` to find all research files.
```

#### 3. Add verify-fix cycle after editing (Impact: Medium)

**Recommended:** After editing, re-run comparison from Step 3 to confirm all drift was resolved.

---

## Item 13: refresh-engineering-baseline (Repo-internal)

**Type:** Skill | **Path:** `.claude/skills/refresh-engineering-baseline/SKILL.md`

### Goal
Update engineering baseline with current web research findings.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | 7-step sequential, measurable criteria |
| Completeness | A | 15% | WebSearch/WebFetch failure handling, user decline, token budget |
| Prompt Engineering | A | 15% | Role priming, structured output, merge example, source quality criteria |
| Context Engineering | B | 15% | Minimal tools; merge example could be reference file |
| Goal Alignment | A | 20% | Source quality gates, spot-check existing, conservative preservation |
| Safety | A | 15% | `disable-model-invocation`, two confirmation gates, "leave unchanged" default |
| Metadata | B | 5% | Complete; no `argument-hint` (takes no args, minor) |
| **Overall** | **A** | **100%** | **Weighted: 91.0** |

### Strengths
- Robust failure handling, conservative safety, evidence quality gates

### Recommendations

#### 1. Consider extracting merge example to reference (Impact: Medium)

The merge decision example in Step 4 could be extracted to `references/merge-examples.md` if merge logic grows more complex.

---

## Item 14: check-repo-health (Repo-internal)

**Type:** Skill | **Path:** `.claude/skills/check-repo-health/SKILL.md`

### Goal
Verify reference freshness, token budgets, and cross-skill reference integrity.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Sequential workflow, conditional checks, sub-checks delineated |
| Completeness | A | 15% | All three check types specified, dashboard template, remediation section |
| Prompt Engineering | B | 15% | Role priming, structured output; lacks mixed-status example |
| Context Engineering | A | 15% | Minimal tools, thresholds externalized, efficient INDEX.md batch read |
| Goal Alignment | A | 20% | Checks align with 90-day cycle, token budgets, CLAUDE.md conventions |
| Safety | A | 10% | Read-only, "never modify" rule |
| Metadata | A | 10% | Complete, accurate |
| **Overall** | **A** | **100%** | **Weighted: 90.4** |

### Strengths
- Externalized thresholds, strong output specification, efficient INDEX.md usage

### Recommendations

#### 1. Remove inline threshold duplication (Impact: Medium)

**Current:**
```
Apply thresholds from `health-thresholds.md`:
- `scoring-rubric.md` — budget: 1000 tokens
- `engineering-baseline.md` — budget: 2000 tokens
- `signal-catalog.md` — budget: 1000 tokens
- Domain cache entries — budget: 500 tokens each
- Other reference files — budget: 500 tokens (default)
```

**Recommended:**
```
Apply thresholds from `health-thresholds.md` (loaded in step 1). Use the file pattern -> budget mapping from the Token Budgets table.
```

#### 2. Add fallback for missing health-thresholds.md (Impact: Medium)

**Recommended:** If the file cannot be read, use built-in defaults and note the fallback in the dashboard header.

---

## Summary

| Item | Type | Overall | Score | Clarity | Completeness | PE | CE | Goal | Safety | Meta |
|------|------|---------|-------|---------|--------------|----|----|------|--------|------|
| review-agent | Skill | A | 95.0 | A | A | A | A | A | A | A |
| review-rule | Skill | A | 95.0 | A | A | A | A | A | A | A |
| review-skill | Skill | A | 93.5 | A | A | A | A | A | B | A |
| review-claude-config | Skill | A | 92.0 | A | A | A | A | A | A | B |
| review-analytics | Skill | A | 91.0 | A | A | B | A | A | A | A |
| refresh-engineering-baseline | Skill | A | 91.0 | A | A | A | B | A | A | B |
| suggest-skills | Skill | A | 91.0 | A | A | A | A | A | B | A |
| apply-rule-review-findings | Skill | A | 90.6 | A | A | B | A | A | A | A |
| apply-skill-review-findings | Skill | A | 90.5 | A | A | B | A | A | A | A |
| check-repo-health | Skill | A | 90.4 | A | A | B | A | A | A | A |
| apply-review-findings | Skill | A | 89.8 | A | A | B | A | A | A | B |
| apply-agent-review-findings | Skill | B | 89.6 | A | A | B | B | A | A | A |
| skill-scaffolding | Skill | B | 88.7 | A | B | B | A | A | A | A |
| research-index | Skill | B | 87.6 | A | B | B | A | B | A | B |

## Cross-Cutting Observations

### Consistent Strengths
- **Safety design is excellent across the board.** Every file-modifying skill has `disable-model-invocation: true` (except suggest-skills -- flagged), confirmation gates, and scope restrictions. Read-only skills use minimal tool sets.
- **Workflow structure is strong.** All 14 skills use numbered sequential steps with explicit conditionals.
- **Reference file separation is well-practiced.** Stable knowledge consistently externalized to `references/` directories.

### Common Anti-Patterns
1. **Missing worked examples in Prompt Engineering.** 7/14 skills scored B on PE for the same reason: no few-shot or worked example showing the core operation.
2. **WebFetch/WebSearch degradation tiers are inconsistent.** Some skills treat the two as independent booleans, others have explicit three-tier fallback.
3. **Git command failure handling is missing.** The three apply skills and orchestrator all run git commands via Bash without failure handling.

### Systemic Recommendations
1. **Add one worked example per skill** to lift PE scores from B to A.
2. **Standardize WebSearch/WebFetch degradation** as a reusable 3-tier pattern.
3. **Add git failure handling** to all apply skills.
4. **Add `disable-model-invocation: true`** to suggest-skills.

## Delta from Prior Review (2026-03-24)

| Item | Dimension | Previous | Current | Change |
|------|-----------|----------|---------|--------|
| review-claude-config | Overall | A (95.0) | A (92.0) | -3.0 |
| review-claude-config | Metadata | A | B | Downgrade |
| suggest-skills | Safety | A | B | Downgrade |
| refresh-engineering-baseline | Overall | A (93.0) | A (91.0) | -2.0 |
| apply-review-findings | Overall | A (93.5) | A (89.8) | -3.7 |
| apply-review-findings | Metadata | A | B | Downgrade |
| skill-scaffolding | Overall | A (92.0) | B (88.7) | -3.3 |
| skill-scaffolding | Overall | A | B | Downgrade |
| check-repo-health | Overall | A (92.0) | A (90.4) | -1.6 |
| check-repo-health | Completeness | B | A | Upgrade |
| review-analytics | Overall | A (91.2) | A (91.0) | -0.2 |
| review-analytics | Completeness | B | A | Upgrade |
| research-index | Overall | A (91.3) | B (87.6) | -3.7 |
| research-index | Overall | A | B | Downgrade |
| research-index | Goal Alignment | A | B | Downgrade |
| research-index | Metadata | A | B | Downgrade |

**New items (not in prior review):** review-skill, review-agent, review-rule, apply-skill-review-findings, apply-agent-review-findings, apply-rule-review-findings (6 items).

**Note on score changes:** The prior review evaluated 8 items; this review evaluates 14 items with stricter rubric application. Score decreases primarily reflect tighter grading on Prompt Engineering (requiring worked examples) and Metadata accuracy (description/body alignment). No skill files were modified between reviews.
