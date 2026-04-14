---
generated_by: review-claude-config
schema_version: 1
date: 2026-04-14
target: /Users/thomaskrahn/workspace/review-claude-config
baseline_version: 2026-04-04
items_reviewed: 3
summary:
  - name: maintain-evidence-layer
    type: Skill
    path: .claude/skills/maintain-evidence-layer/SKILL.md
    overall: B
    score: 87.4
    clarity: B
    completeness: B
    prompt_engineering: A
    context_engineering: A
    goal_alignment: A
    safety: B
    metadata: B
  - name: refresh-engineering-baseline
    type: Skill
    path: .claude/skills/refresh-engineering-baseline/SKILL.md
    overall: A
    score: 93.0
    clarity: A
    completeness: A
    prompt_engineering: A
    context_engineering: A
    goal_alignment: A
    safety: B
    metadata: B
  - name: sync-research-index
    type: Skill
    path: .claude/skills/sync-research-index/SKILL.md
    overall: B
    score: 88.4
    clarity: A
    completeness: B
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: B
    metadata: A
---

## Per-Item Reports

---

### .claude/skills/maintain-evidence-layer/SKILL.md

#### Goal
Audit the evidence layer for label normalization, source freshness, contradiction recording, and tier compliance on a 90-day cadence.

#### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | B | 15% | WS-1/WS-2/RD-5 PASS; WS-3 FAIL: Steps 3-6 lack parallel/sequential annotation despite being independent scope-gated checks |
| Completeness | B | 15% | AH-1/AH-2 PASS; AH-3 FAIL: no error handling for invalid --scope values |
| Prompt Engineering | A | 15% | OF-1 PASS (literal report template), role priming ("evidence layer auditor"), constraint specification (Hard Rules), evidence-first framing (provenance as primary audit goal) |
| Context Engineering | A | 15% | PD-1/PD-2/PD-3 PASS; 288 lines, minimal tool set, JIT loading of reference files at point of use |
| Goal Alignment | A | 20% | Four complementary checks (labels, freshness, contradictions, tiers); provenance map integration; 90-day cadence aligns with repo convention |
| Safety | B | 15% | SP-1/RL-1/RL-4/RL-9 PASS; SP-2 FAIL: AskUserQuestion used 3x but absent from allowed-tools; Write scoped to `.claude/reviews/` only |
| Metadata | B | 5% | PD-5/AH-4/RD-1/RD-2/RD-3 PASS; SP-2 FAIL impacts tool list accuracy |
| **Overall** | **B** | **100%** | **Weighted: 87.4** |

#### Strengths
- Comprehensive four-check audit covering labels, freshness, contradictions, and tier compliance
- Strong provenance map integration in Step 6 reflecting actual repo architecture
- Thoughtful trigger condition check (Step 2) preventing unnecessary runs within 90-day window

#### Reliability Diagnostics

##### Activation
No activation issues detected. RD-1/RD-2/RD-3 all PASS.

##### Execution
- **RD-6 FAIL**: No explicit tool availability check before first use. Mitigated by `disable-model-invocation: true` harness context. Low severity.

#### Recommendations

##### 1. Add error handling for invalid --scope values (Impact: Medium, Category: Workflow, ID: AH-3:.claude/skills/maintain-evidence-layer/SKILL.md:Compl/v1)

**Evidence:** Argument Handling section accepts `--scope` with enum values but does not define behavior for unrecognized values. A user passing `--scope typo` hits undefined behavior.

**Why it matters:** Unvalidated enum input can lead to silent no-op or confusing error downstream.

**Validation:** Pass `--scope typo` and confirm the skill produces a clear error message and halts.

**Current:**
```
Parse `$ARGUMENTS` for `--scope` followed by one of: `all`, `labels`, `freshness`,
`contradictions`, `tiers`. If not provided or `all`, run all four checks.
```

**Recommended:**
```
Parse `$ARGUMENTS` for `--scope` followed by one of: `all`, `labels`, `freshness`,
`contradictions`, `tiers`. If not provided or `all`, run all four checks.
If `--scope` is provided with an unrecognized value, report:
"Unrecognized scope: [value]. Valid options: all, labels, freshness, contradictions, tiers." and stop.
```

##### 2. Add AskUserQuestion to allowed-tools (Impact: Medium, Category: Metadata, ID: SP-2:.claude/skills/maintain-evidence-layer/SKILL.md:Safety/v1)

**Evidence:** `allowed-tools: Read, Write, Glob, Grep` but the body uses `AskUserQuestion` in Steps 2, 8, and 9.

**Why it matters:** Tool list mismatch reduces metadata accuracy and could cause runtime errors if the harness enforces declared tool lists strictly.

**Validation:** Confirm AskUserQuestion appears in both allowed-tools and the workflow body.

**Current:**
```
allowed-tools: Read, Write, Glob, Grep
```

**Recommended:**
```
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
```

##### 3. Add parallel/sequential annotation to Phase 2 (Impact: Low, Category: Workflow, ID: WS-3:.claude/skills/maintain-evidence-layer/SKILL.md:Clarity/v1)

**Evidence:** Steps 3-6 are independent scope-gated checks but lack explicit execution order annotation.

**Why it matters:** Without annotation, an agent may execute checks in an unexpected order.

**Validation:** Confirm Phase 2 header includes explicit execution order guidance.

**Current:**
```
## Phase 2 — Checks
```

**Recommended:**
```
## Phase 2 — Checks

Run only the steps matching the --scope flag (or all four when scope is `all`). Execute sequentially.
```

---

### .claude/skills/refresh-engineering-baseline/SKILL.md

#### Goal
Update the engineering baseline reference file with current prompt, context, and tool-design best practices from web research.

#### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | WS-1/WS-2/RD-5 PASS; all steps numbered with explicit dependencies; all conditionals have concrete triggers |
| Completeness | A | 15% | AH-1/AH-2/OF-1/OF-2/AP-4 PASS; thorough WebSearch failure handling (3 scenarios), WebFetch fallback, file-not-found stop |
| Prompt Engineering | A | 15% | Role priming ("research librarian"), structured output template (Step 7), explicit constraints (2K tokens, three sections), verification criteria (spot-check 2-3), evidence-first merge with worked example |
| Context Engineering | A | 15% | 167 lines; minimal tool set (4 tools); all references loaded JIT via Read in Step 1; WebFetch probed before use |
| Goal Alignment | A | 20% | Freshness gate prevents churn; source quality criteria applied; deduplication; evidence classification; provenance tracking; conservative removal policy; confirmation before writes |
| Safety | B | 15% | SP-1/SP-3/SP-4 PASS; Tier A (Write+WebSearch/WebFetch) justified by confirmation gates; SP-2 FAIL: AskUserQuestion not in allowed-tools |
| Metadata | B | 5% | Complete frontmatter; description accurate with exclusion clause; AP-2 FAIL: AskUserQuestion not declared |
| **Overall** | **A** | **100%** | **Weighted: 93.0** |

#### Strengths
- Exceptionally thorough WebSearch failure handling with three distinct scenarios and graceful degradation
- Conservative merge policy with worked example showing how to handle conflicting evidence
- Dual-file update (baseline + provenance map) ensures source traceability

#### Reliability Diagnostics

##### Activation
No activation issues detected. RD-1/RD-2/RD-3 all PASS.

##### Execution
- **RD-6 PASS**: WebFetch availability probed in Step 1 before use in Step 3.5.
- RD-4/RD-5 PASS.

#### Recommendations

##### 1. Add AskUserQuestion to allowed-tools (Impact: Medium, Category: Metadata, ID: SP-2:.claude/skills/refresh-engineering-baseline/SKILL.md:Safety/v1)

**Evidence:** `allowed-tools: WebSearch, WebFetch, Read, Write` but `AskUserQuestion` is used in Steps 2 and 5 for confirmation gates.

**Why it matters:** Tool list mismatch reduces metadata accuracy; if the harness enforces declared tool lists, confirmation gates would fail.

**Validation:** Confirm AskUserQuestion appears in both allowed-tools and the workflow body.

**Current:**
```
allowed-tools: WebSearch, WebFetch, Read, Write
```

**Recommended:**
```
allowed-tools: WebSearch, WebFetch, Read, Write, AskUserQuestion
```

##### 2. Add sequential annotation to Step 3 queries (Impact: Low, Category: Workflow, ID: WS-3:.claude/skills/refresh-engineering-baseline/SKILL.md:Clarity/v1)

**Evidence:** Step 3 WebSearch queries have early-termination logic implying sequential execution but no explicit marker.

**Why it matters:** Without annotation, an agent could parallelize queries and miss the early-termination optimization.

**Validation:** Confirm Step 3 includes "Run queries sequentially" annotation.

**Current:**
```
Run these WebSearch queries (replace `[current year]` with the actual year).
```

**Recommended:**
```
Run these WebSearch queries sequentially (early termination requires evaluating each before proceeding). Replace `[current year]` with the actual year.
```

---

### .claude/skills/sync-research-index/SKILL.md

#### Goal
Detect and fix drift between research files on disk and CLAUDE.md Research References section.

#### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | WS-1/WS-2/WS-3/RD-5 PASS; all steps numbered with explicit stop gates and concrete conditionals |
| Completeness | B | 15% | AH-1/AH-2/AH-3/OF-1 PASS; AP-4 FAIL: no error handling for Edit/Read tool failures; OF-2: STALE missing from report template |
| Prompt Engineering | B | 15% | Role priming ("index maintainer"), structured output template, explicit constraints (Hard Rules); missing few-shot example of parsed entry format |
| Context Engineering | A | 15% | 96 lines; minimal tools (Read, Edit, Glob); no inlined knowledge; JIT reading of research files |
| Goal Alignment | A | 20% | Four-status classification (OK/UNLINKED/BROKEN/STALE); confirmation before mutation; commit suggestion follows repo convention |
| Safety | B | 15% | SP-1/RL-4/RL-9 PASS; SP-3/RL-1 FAIL: re-comparison loop in Step 5 lacks iteration bound |
| Metadata | A | 5% | Complete frontmatter; description matches body; argument-hint accurate; explicit exclusion clause |
| **Overall** | **B** | **100%** | **Weighted: 88.4** |

#### Strengths
- Exceptionally compact at 96 lines — minimal instruction surface for a well-defined task
- Clean four-status classification (OK/UNLINKED/BROKEN/STALE) covers all drift scenarios
- Hard Rules section provides clear safety boundaries

#### Reliability Diagnostics

##### Activation
No activation issues detected. RD-1/RD-2/RD-3 all PASS.

##### Execution
- **RD-4 FAIL**: Only covers "not found" cases. No handling for Edit tool errors or malformed CLAUDE.md entries.

#### Recommendations

##### 1. Bound the re-comparison loop (Impact: Medium, Category: Safety, ID: SP-3:.claude/skills/sync-research-index/SKILL.md:Safety/v1)

**Evidence:** Step 5: "re-run the comparison from Step 3. If drift remains, report and offer to fix." No iteration limit.

**Why it matters:** Unbounded loops violate R1 (termination conditions) — a High reliability check and B/C discriminator.

**Validation:** Verify Step 5 includes a max-iteration clause.

**Current:**
```
After editing, re-run the comparison from Step 3 against the updated CLAUDE.md. If drift remains, report the remaining issues and offer to fix. Otherwise, confirm: "All drift resolved."
```

**Recommended:**
```
After editing, re-run the comparison from Step 3 against the updated CLAUDE.md (at most once). If drift remains after one fix cycle, report the remaining issues to the user and stop — do not attempt further fixes without user confirmation. Otherwise, confirm: "All drift resolved."
```

##### 2. Add error handling for Edit/Read failures (Impact: Medium, Category: Workflow, ID: AP-4:.claude/skills/sync-research-index/SKILL.md:Compl/v1)

**Evidence:** No guidance on what happens if Edit fails (non-unique string match) or Read fails on a research file.

**Why it matters:** Edit tool fails on non-unique `old_string` matches. CLAUDE.md entries may have similar formatting.

**Validation:** Verify workflow includes at least one "If Edit/Read fails..." recovery clause.

**Current:**
```
Use Edit to make targeted changes to the `## Research References` section only. Never modify other sections.
```

**Recommended:**
```
Use Edit to make targeted changes to the `## Research References` section only. Never modify other sections. If Edit fails (e.g., non-unique match), report the specific entry that could not be updated to the user and continue with remaining entries.
```

##### 3. Add STALE to report template (Impact: Low, Category: Output, ID: OF-2:.claude/skills/sync-research-index/SKILL.md:Compl/v1)

**Evidence:** Step 3 defines STALE status but the template in Step 4 only shows OK, UNLINKED, and BROKEN examples.

**Why it matters:** Incomplete template may cause the agent to omit STALE entries from the report.

**Validation:** Verify report template includes a STALE row example.

##### 4. Align description with actual behavior (Impact: Low, Category: Metadata, ID: RD-4:.claude/skills/sync-research-index/SKILL.md:Compl/v1)

**Evidence:** Description says "description mismatches" but STALE classification only checks title mismatch.

**Why it matters:** Description promises functionality that doesn't exist.

**Validation:** Confirm either Step 3 adds description comparison or description says "title mismatches."

---

## Summary

| Item | Type | Overall | Clarity | Completeness | PE | CE | Goal | Safety | Meta |
|------|------|---------|---------|--------------|----|----|------|--------|------|
| maintain-evidence-layer | Skill | B (87.4) | B | B | A | A | A | B | B |
| refresh-engineering-baseline | Skill | A (93.0) | A | A | A | A | A | B | B |
| sync-research-index | Skill | B (88.4) | A | B | B | A | A | B | A |

## Cross-Cutting Observations

**1. AskUserQuestion consistently undeclared in allowed-tools.** All three skills use `AskUserQuestion` for confirmation gates but none declare it in frontmatter `allowed-tools`. This is the single most common finding across the portfolio. Whether this is a real gap depends on whether the Claude Code harness enforces declared tool lists for `AskUserQuestion` — if it does, all three skills would fail at their confirmation gates. Fix all three simultaneously.

**2. Strong context engineering across all items.** All three skills are compact (96-288 lines), use minimal tool sets aligned to their archetypes, and load references JIT. This is a consistent strength.

**3. Parallel/sequential annotations missing in two skills.** Both `maintain-evidence-layer` (Steps 3-6) and `refresh-engineering-baseline` (Step 3 queries) have implicit execution order that should be explicit. Low severity but easy to fix.

**4. Safety grades capped at B by tool list metadata, not by actual safety posture.** All three skills have proper confirmation gates, scoped writes, and stop conditions. The B grades in Safety come primarily from the AskUserQuestion metadata gap, not from genuine safety risk.

**5. Prior review (2026-04-06) scored all items at A.** The current review applies stricter scrutiny to tool list accuracy (SP-2) and error handling completeness (AH-3, AP-4, SP-3). The grade changes reflect rubric enforcement, not skill degradation — no files were modified between reviews.

## Delta from Prior Review (2026-04-06)

| Item | Dimension | Previous | Current | Change |
|------|-----------|----------|---------|--------|
| maintain-evidence-layer | Overall | A (92.0) | B (87.4) | -1 grade |
| maintain-evidence-layer | Clarity | A | B | -1 grade |
| maintain-evidence-layer | Safety | A | B | -1 grade |
| maintain-evidence-layer | Metadata | A | B | -1 grade |
| refresh-engineering-baseline | Safety | A | B | -1 grade |
| refresh-engineering-baseline | Metadata | A | B | -1 grade |
| sync-research-index | Overall | A (95.0) | B (88.4) | -1 grade |
| sync-research-index | Completeness | A | B | -1 grade |
| sync-research-index | Prompt Engineering | A | B | -1 grade |
| sync-research-index | Safety | A | B | -1 grade |
