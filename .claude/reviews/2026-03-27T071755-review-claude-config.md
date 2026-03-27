---
generated_by: review-claude-config
schema_version: 1
date: 2026-03-27
target: /Users/ntbc/workspace/claude/review-claude-config
baseline_version: 2026-03-26
items_reviewed: 2
summary:
  - name: sync-research-index
    type: Skill
    path: .claude/skills/sync-research-index/SKILL.md
    overall: B
    score: 89.6
    clarity: A
    completeness: B
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: B
  - name: refresh-engineering-baseline
    type: Skill
    path: .claude/skills/refresh-engineering-baseline/SKILL.md
    overall: A
    score: 91.2
    clarity: A
    completeness: A
    prompt_engineering: A
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: B
---

## sync-research-index

### Goal
Detect and fix drift between research files on disk and the CLAUDE.md Research References section.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Explicit numbered workflow with deterministic classification scheme and clear stop conditions |
| Completeness | B | 15% | Four classification states cover core cases; STALE items detected but not fixed in sync actions |
| Prompt Engineering | B | 15% | Role priming, structured output template, constraints, verification via re-run; missing few-shot examples |
| Context Engineering | A | 15% | Minimal 3-tool set, JIT retrieval (5 lines for titles, full read only when needed) |
| Goal Alignment | A | 20% | Domain-appropriate discover→parse→compare→report→fix→verify workflow with convergence loop |
| Safety | A | 15% | `disable-model-invocation`, least-privilege tools, section-scoped edits, confirmation gate |
| Metadata | B | 5% | Complete frontmatter; description omits STALE classification feature |
| **Overall** | **B** | **100%** | **Weighted: 89.6** |

### Strengths
- **Excellent safety posture** — `disable-model-invocation`, no Bash/Write, section-scoped editing, report-before-modify pattern
- **Clean context engineering** — Exactly 3 tools (Read, Edit, Glob), JIT title extraction avoids unnecessary reads
- **Self-verifying workflow** — Re-runs comparison after edits to ensure convergence

### Recommendations

#### 1. Handle STALE items in sync actions (Impact: Medium, Category: Workflow)
**Evidence:** Step 3 classifies STALE items (title mismatch between file heading and CLAUDE.md entry), but Step 5 only describes actions for UNLINKED and BROKEN items. STALE drift is detected and reported but never fixed.

**Why it matters:** Users who agree to sync expect all reported drift to be resolved. Silently skipping STALE items breaks the convergence guarantee.

**Validation:** Re-review Step 5 to confirm all four classification states have corresponding sync actions.

**Current:**
```
If yes:
- **For UNLINKED files:** Read each file to extract its title and a one-line summary. Add an entry...
- **For BROKEN links:** Remove the entry from the Research References section.
```

**Recommended:**
```
If yes:
- **For UNLINKED files:** Read each file to extract its title and a one-line summary. Add an entry to the Research References section following the existing format: `- [Title](relative/path) — Description`
- **For BROKEN links:** Remove the entry from the Research References section.
- **For STALE entries:** Update the title in the CLAUDE.md entry to match the file's current `# ` heading.
```

#### 2. Clarify interactive prompt mechanism (Impact: Medium, Category: Safety)
**Evidence:** Step 5 uses `Ask: "Update CLAUDE.md Research References section to fix drift? (yes/no)"`. Per CLAUDE.md, `AskUserQuestion` silently auto-completes with empty answers in plugin skills loaded via the Skill tool.

**Why it matters:** If interpreted as `AskUserQuestion`, the skill could auto-approve modifications without user consent.

**Validation:** Confirm Step 5 uses explicit "Print and wait" wording consistent with workflow menu convention.

**Current:**
```
Ask: "Update CLAUDE.md Research References section to fix drift? (yes/no)"
```

**Recommended:**
```
Print the following and wait for the user's response:
"Update CLAUDE.md Research References section to fix drift? (yes/no)"
```

#### 3. Add malformed entry handling (Impact: Low, Category: Completeness)
**Evidence:** Step 2 parses CLAUDE.md entries expecting `- [Title](path) — Description` format with no fallback for non-conforming entries.

**Why it matters:** Malformed entries could cause silent data loss or incorrect classification.

**Validation:** Confirm Step 2 defines MALFORMED classification and drift report includes it.

**Current:**
```
Parse each entry in the section. Expected format:
- [Title](relative/path) — Description
Extract for each entry: title, relative path, description.
```

**Recommended:**
```
Parse each entry in the section. Expected format:
- [Title](relative/path) — Description

Extract for each entry: title, relative path, description. If an entry does not match this format, classify it as **MALFORMED** and include it in the drift report with detail "Entry format not recognized". Do not modify malformed entries during sync.
```

---

## refresh-engineering-baseline

### Goal
Update the engineering baseline reference file with current best practices from web research, applying rigorous source quality criteria.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Numbered sequential workflow, deterministic conditionals, explicit binary branching at every gate |
| Completeness | A | 15% | Three-tier WebSearch degradation, token budget overflow handling, early-termination heuristic |
| Prompt Engineering | A | 15% | Role priming, structured output template, few-shot merge example, evidence-gated source criteria |
| Context Engineering | A | 15% | 4-tool minimal set, JIT retrieval, tiered WebFetch caps at 6-9, 2K token budget enforcement |
| Goal Alignment | A | 20% | Source quality criteria, deduplication, spot-checking, merge routing aligned with baseline structure |
| Safety | A | 15% | Two confirmation gates, `disable-model-invocation`, explicit stop at every failure, no-Bash |
| Metadata | B | 5% | Complete frontmatter; no `argument-hint` (low impact — skill takes no arguments) |
| **Overall** | **A** | **100%** | **Weighted: 91.2** |

### Strengths
- **Robust degradation ladder** — Three-tier WebSearch failure handling with specific user messaging at each level
- **Evidence-gated merge process** — Source quality criteria (credible + actionable + cross-validated) with explicit discard categories
- **Two-tier WebFetch strategy** — Coverage-first, depth-second design balances thoroughness against context budget

### Recommendations

#### 1. Document query-rubric coverage intent (Impact: Medium, Category: Workflow)
**Evidence:** CLAUDE.md states "queries must cover all rubric dimensions." Current 6 queries cover Clarity, PE, CE, Safety, Goal Alignment. Completeness and Metadata have no corresponding queries or routing rules.

**Why it matters:** The invariant is explicit. Either the gap should be closed or the rationale for exclusion documented.

**Validation:** Confirm Step 4 includes routing for Completeness/Metadata or explicitly explains why these are excluded.

**Current:**
```
For each section (Prompt Engineering, Context Engineering, Tool Design):
- Route safety and guardrail techniques to Context Engineering
- Route instruction clarity techniques to Prompt Engineering
- Route agentic workflow techniques to the best-fit section
```

**Recommended:**
```
For each section (Prompt Engineering, Context Engineering, Tool Design):
- Route safety and guardrail techniques to Context Engineering
- Route instruction clarity techniques to Prompt Engineering
- Route agentic workflow techniques to the best-fit section
Note: Completeness and Metadata are structural evaluation dimensions assessed via the rubric, not technique-driven domains. They do not require dedicated research queries.
```

#### 2. Normalize step numbering (Impact: Low, Category: Workflow)
**Evidence:** Step 3.5 breaks the integer numbering convention used by all other steps (1-7).

**Validation:** Confirm all steps use consistent integer or sub-step numbering.

#### 3. Standardize baseline file path references (Impact: Low, Category: Clarity)
**Evidence:** Step 1 uses `skills/review-claude-config/references/engineering-baseline.md` while the intro says `references/engineering-baseline.md` — both relative, neither anchored.

**Validation:** Confirm a single consistent path reference throughout.

---

## Summary

| Item | Type | Overall | Clarity | Completeness | PE | CE | Goal | Safety | Meta |
|------|------|---------|---------|--------------|----|----|------|--------|------|
| sync-research-index | Skill | B (89.6) | A | B | B | A | A | A | B |
| refresh-engineering-baseline | Skill | A (91.2) | A | A | A | A | A | A | B |

## Cross-Cutting Observations

**Consistent strengths:**
- Both skills have strong safety postures with `disable-model-invocation: true`, confirmation gates, and least-privilege tool sets
- Both use structured output templates and role priming effectively
- Both handle failure modes explicitly rather than relying on implicit model behavior

**Common pattern — Metadata B ceiling:**
- Both skills score B on Metadata for minor gaps (missing STALE mention in description, missing `argument-hint`). Neither gap is significant enough to justify a separate finding, but awareness may prevent recurrence in future skills.

**Interactive prompt ambiguity:**
- `sync-research-index` uses `Ask:` wording that could be misinterpreted as an `AskUserQuestion` call. Both skills would benefit from the explicit "Print and wait" pattern documented in the project's workflow menu convention.

## Delta from Prior Review (2026-03-25)

| Item | Dimension | Previous | Current | Change |
|------|-----------|----------|---------|--------|
| sync-research-index | Completeness | B | B | — |
| sync-research-index | Prompt Engineering | B | B | — |
| sync-research-index | Context Engineering | A | A | — |
| sync-research-index | Goal Alignment | B | A | +1 |
| sync-research-index | Metadata | B | B | — |
| sync-research-index | Overall | B (87.6) | B (89.6) | +2.0 |
| refresh-engineering-baseline | Context Engineering | B | A | +1 |
| refresh-engineering-baseline | Overall | A (91.0) | A (91.2) | +0.2 |

Note: Prior review tracked sync-research-index as `research-index` at path `.claude/skills/research-index/SKILL.md` (renamed since).
