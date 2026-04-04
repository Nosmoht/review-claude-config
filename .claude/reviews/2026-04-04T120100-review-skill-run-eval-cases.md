---
generated_by: review-skill
schema_version: 1
date: 2026-04-04
target: /Users/ntbc/workspace/review-claude-config/skills/run-eval-cases/SKILL.md
baseline_version: 2026-04-03
items_reviewed: 1
summary:
  - name: run-eval-cases
    type: Skill
    path: skills/run-eval-cases/SKILL.md
    overall: B
    score: 84.5
    clarity: B
    completeness: C
    prompt_engineering: B
    context_engineering: B
    goal_alignment: A
    safety: C
    metadata: A
---

# Review: run-eval-cases

## Goal
Execute regression tests against the review system after changes to the rubric, baseline, reviewer prompts, analytics logic, or scaffold workflow, producing per-criterion PASS/FAIL verdicts and an overall CLEAN/REGRESSION verdict.

## Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | B | 15% | Workflow is explicit and deterministic; Case 4's dual execution modes (plugin + maintenance) lack explicit "run both" marker |
| Completeness | C | 15% | Missing bounded execution for agent launches, pre-run state capture for Case 4 revert, and stale eval-temp detection |
| Prompt Engineering | B | 15% | Role priming, sprint contracts, structured output, and Hard Rules present; no few-shot criterion-check examples |
| Context Engineering | B | 15% | Subagent isolation and compaction checkpoint are strong; 5 synthetic artifacts inlined at 170 lines adds bulk regardless of case selection |
| Goal Alignment | A | 20% | Sprint contracts tightly aligned with review-eval-cases.md; all 5 cases map correctly to documented expected behaviors |
| Safety | C | 15% | No confirmation gate before Case 4 scaffold writes to production dirs; rm -rf scope unverified; no agent execution timeout |
| Metadata | A | 5% | All frontmatter fields present, accurate, and correctly configured including disable-model-invocation |
| **Overall** | **B** | **100%** | **Weighted: 84.5 → B** |

## Strengths
- Sprint contract pattern (define acceptance criteria before execution) is sound test methodology — prevents post-hoc rationalization of results.
- BLOCKED vs FAIL distinction is explicit and well-reasoned, preserving partial results when skills are missing.
- Compaction checkpoint after case execution is a genuine context engineering win for a 5-case orchestration run.
- `disable-model-invocation: true` is correctly applied for a test runner that should not be invoked as a prompted skill.
- Case 5 (Reliability Pattern Detection) acceptance criteria are specific enough to catch grade inflation — requiring circuit breaker or progressive fallback in the Recommended block, not just generic safety advice.

## Recommendations

### 1. Add Bounded Execution for Agent Launches (Impact: High, Category: Safety)

**Evidence:** Cases 1, 2, 3, 4, 5 all contain `Launch an Agent (allowed-tools: ...) to run /review-skill ...` with no timeout, retry limit, or failure budget. The Hard Rule "If a Phase 2 agent fails entirely... mark that case FAIL" does not bound how long the skill waits.

**Why it matters:** The engineering baseline requires bounded execution for Safety A. An agent that hangs will block the entire eval run indefinitely. Retry ceilings are a baseline-documented Repo default pattern.

**Validation:** On re-review, Phase 2 or Hard Rules should include an explicit agent timeout/cap; each Agent launch should reference it.

**Current:**
```
Launch an Agent (allowed-tools: Read, Glob, WebSearch, WebFetch, Write, Bash) to run `/review-skill .claude/eval-temp/eval-test-real-issue/SKILL.md`
```

**Recommended:**
```
Launch an Agent (allowed-tools: Read, Glob, WebSearch, WebFetch, Write, Bash) to run `/review-skill .claude/eval-temp/eval-test-real-issue/SKILL.md`. If the agent does not complete within a reasonable time or errors without producing output, mark the case FAIL for all criteria with reason "agent-error: no output" and continue to the next case. Do not retry.
```

---

### 2. Capture Pre-Run State Before Case 4 Agent Launch (Impact: High, Category: Workflow)

**Evidence:** Case 4 Cleanup says "revert any doc changes... using Edit or by reading the pre-run content and restoring it." But Execution step 1 only captures timestamps — not actual content of README.md and CLAUDE.md before the scaffold agent runs.

**Why it matters:** After the scaffold agent runs, original content is gone. A timestamp comparison cannot restore it. The pre-run content must be captured before the Agent launch.

**Validation:** On re-review, Case 4 setup should include Read of README.md and CLAUDE.md before Agent launch, with instructions to store content for restoration.

**Current:**
```
1. Note the current last-modified timestamps of `README.md` and `CLAUDE.md` via Bash
2. Launch an Agent...
```

**Recommended:**
```
1. Read `README.md` and store its full content as `readme_pre_run`.
2. Read `CLAUDE.md` and store its full content as `claude_md_pre_run`.
3. Note the current last-modified timestamps via Bash (for criterion verification).
4. Launch an Agent...

**Cleanup:**
Restore `README.md` to `readme_pre_run` using Write if it was modified. Restore `CLAUDE.md` to `claude_md_pre_run` using Write if it was modified. If either restore fails, report the failure.
```

---

### 3. Check for Stale eval-temp Before Writing Artifacts (Impact: Medium, Category: Workflow)

**Evidence:** Phase 2 writes synthetic artifacts to `.claude/eval-temp/` with no prior check. A previous failed run could leave stale artifacts that contaminate test results.

**Why it matters:** Stale artifacts from a prior interrupted run could cause Cases 1, 2, or 5 to evaluate a different skill than the intended synthetic one.

**Validation:** On re-review, Phase 1 Setup should include a pre-clean `rm -rf .claude/eval-temp` or explicit Glob check with decision branch.

**Current:**
```
### Step 1: Load eval definitions

Read `docs/review-eval-cases.md`. For each selected case...
```

**Recommended:**
```
### Step 1: Pre-clean

Run `rm -rf .claude/eval-temp` to remove any stale artifacts from a previous interrupted run. If the directory does not exist, note and continue.

### Step 2: Load eval definitions
...
```

---

### 4. Remove WebSearch/WebFetch from Eval Agent Tool Sets (Impact: Medium, Category: Safety)

**Evidence:** Cases 1, 2, and 5 launch agents with `allowed-tools: Read, Glob, WebSearch, WebFetch, Write, Bash`. Web research introduces non-determinism into what should be deterministic regression tests.

**Why it matters:** Case 2 (Cosmetic Non-Overstatement) could flip from PASS to FAIL if a web search returns new domain evidence. Least-privilege tool scoping is also a Safety rubric criterion.

**Validation:** On re-review, eval agent tool sets should exclude WebSearch and WebFetch; review skills degrade gracefully to model knowledge when web tools are absent.

**Current:**
```
Launch an Agent (allowed-tools: Read, Glob, WebSearch, WebFetch, Write, Bash) to run `/review-skill ...`
```

**Recommended:**
```
Launch an Agent (allowed-tools: Read, Glob, Write, Bash) to run `/review-skill ...`. Exclude WebSearch and WebFetch to ensure deterministic results — the review skill degrades gracefully to model knowledge when web tools are absent.
```

---

### 5. Add Explicit "Run Both Modes" Marker to Case 4 (Impact: Low, Category: Workflow)

**Evidence:** Case 4 has two `Execution` sub-sections with no explicit instruction that both must always run when Case 4 is selected.

**Why it matters:** A model could interpret the two sections as alternatives rather than sequential requirements.

**Validation:** On re-review, Case 4 should have a one-line preamble before the first Execution section.

**Current:**
```
**Execution (plugin mode):**

1. Note the current last-modified timestamps...
```

**Recommended:**
```
Both execution modes (plugin and maintenance) run as part of Case 4. Run plugin mode first, then maintenance mode.

**Execution (plugin mode):**

1. Note the current last-modified timestamps...
```

---

## Reference File Recommendation

The five synthetic artifact definitions (Cases 1–5) are fully inlined and together occupy approximately 170 lines regardless of which cases are selected. Extracting them to `references/eval-artifacts.md` and loading them JIT (Read only the relevant section for each selected case) would reduce context budget by ~40% when running a single case.
