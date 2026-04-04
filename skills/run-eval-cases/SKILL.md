---
name: run-eval-cases
description: >
  Run regression test cases against the review system to verify correctness
  after changing the rubric, shared baseline, reviewer prompts, analytics
  logic, or scaffold workflow. Executes up to 5 synthetic eval cases and
  produces a PASS/FAIL verdict per criterion. Use after changing rubric,
  baseline, reviewer prompts, analytics logic, or scaffold workflow.
argument-hint: "[1-5|all|case1,case3]"
allowed-tools: Agent, Read, Write, Glob, Edit, Bash
disable-model-invocation: true
---

# Run Eval Cases

You are a regression test runner for the review system. Your job is to execute synthetic test cases, compare actual output against predefined acceptance criteria, and report a verdict. You define acceptance criteria before running each case, then measure actual output against them. This is the sprint contract pattern: specify what success looks like, then verify it.

## Argument Handling

Parse `$ARGUMENTS`:
- Empty or `all` → run all 5 cases
- Single digit `1`–`5` → run that case only
- Comma-separated like `case1,case3` or `1,3` → run the listed cases

If the argument cannot be parsed as a valid case selection, default to `all` and note the fallback.

## Phase 1 — Setup

### Step 0: Pre-clean eval workspace

Run via Bash: `rm -rf .claude/eval-temp && mkdir -p .claude/eval-temp`

This prevents stale artifacts from prior runs affecting the current execution. If the removal fails, report the error and stop — do not write over potentially important leftover files.

### Step 1: Load eval definitions

Read `docs/review-eval-cases.md`. For each selected case, note the artifact description and expected behavior assertions to cross-check against the sprint contracts below.

### Step 2: Verify required skills

Glob for the following SKILL.md files:

- `skills/review-skill/SKILL.md`
- `skills/review-agent/SKILL.md`
- `skills/review-analytics/SKILL.md`
- `skills/scaffold-skill/SKILL.md`

If any file is missing, report which skill is absent and which cases depend on it. If a skill required for a selected case is missing, mark that case as BLOCKED and continue with remaining cases. If all required skills are missing, report and stop.

## Phase 2 — Case Execution

For each selected case, evaluate the sprint contract criteria against the actual output. Record PASS or FAIL per criterion with a cited excerpt from the output.

---

### Case 1: Real Issue Detection

**Sprint contract — acceptance criteria (defined before execution):**

- C1-1: At least one finding has `Impact: High` or `Impact: Medium`
- C1-2: At least one finding has an `Evidence:` field with text tied to the artifact
- C1-3: At least one finding has a `Validation:` field
- C1-4: At least one finding has both `Current:` and `Recommended:` blocks

**Synthetic artifact — write exactly this content to `.claude/eval-temp/eval-test-real-issue/SKILL.md`:**

```markdown
---
name: eval-test-real-issue
description: Manages deployments.
allowed-tools: Read, Write, Edit, Glob
---

# Eval Test Real Issue

## Workflow

### Step 1
Find all relevant files using Glob.

### Step 2
Edit the configuration as needed using Write.

### Step 3
Report the result.
```

**Execution:**

1. Write the synthetic artifact above to `.claude/eval-temp/eval-test-real-issue/SKILL.md`
2. Launch an Agent (allowed-tools: Read, Glob, Write, Bash) to run `/review-skill .claude/eval-temp/eval-test-real-issue/SKILL.md`. If the agent does not return within a reasonable time or errors out, mark all C1-* criteria as FAIL with note "agent timeout or crash" and proceed to the next case. Do not retry.
3. Capture the full output
4. Check each criterion against the output and record PASS/FAIL with a one-sentence excerpt

---

### Case 2: Cosmetic Non-Overstatement

**Sprint contract — acceptance criteria (defined before execution):**

- C2-1: No finding claims the skill is "unsafe" without citing specific evidence from the artifact
- C2-2: No finding claims structural incompleteness without citing specific evidence from the artifact
- C2-3: All findings are `Impact: Low` or absent (no Medium or High findings)

**Synthetic artifact — write exactly this content to `.claude/eval-temp/eval-test-cosmetic/SKILL.md`:**

```markdown
---
name: eval-test-cosmetic
description: >
  Analyzes repository structure and produces a health summary. Use when
  you need a structured overview of the current state of a repository.
allowed-tools: Read, Glob
disable-model-invocation: true
---

# Eval Test Cosmetic

You are a repository analyzer. Your job is to inspect a given folder and summarize its structure.

## Argument Handling

Parse `$ARGUMENTS` as the target folder path. If empty, use the current working directory.

## Workflow

### Step 1: Discover files

Use Glob to list all Markdown files under the target folder.

### Step 2: Read structure

Read the top-level README.md if present. Note the primary sections.

### Step 3: Identify patterns

Look for recurring directory names that suggest a known layout (e.g., `src/`, `docs/`, `tests/`).

### Step 4: Summarize

Produce a brief summary in this format:

```
## Repository Summary
- **Target:** [path]
- **Markdown files:** [count]
- **Layout pattern:** [detected or "none"]
- **README present:** [yes/no]
```

### Step 5: Present

Output the summary. The report should then be generated by the skill after completion of all steps.

## Hard Rules

- Read-only. Never modify any file.
- If the target folder does not exist, report and stop.
```

**Execution:**

1. Write the synthetic artifact above to `.claude/eval-temp/eval-test-cosmetic/SKILL.md`
2. Launch an Agent (allowed-tools: Read, Glob, Write, Bash) to run `/review-skill .claude/eval-temp/eval-test-cosmetic/SKILL.md`. If the agent does not return or errors out, mark all C2-* criteria as FAIL with note "agent timeout or crash" and proceed.
3. Capture the full output
4. Check each criterion against the output and record PASS/FAIL with a one-sentence excerpt

---

### Case 3: Analytics Rename/Move Detection

**Sprint contract — acceptance criteria (defined before execution):**

- C3-1: Items are tracked by `type + path`, not by `name` alone
- C3-2: The new path (`skills/foo-baz/SKILL.md`) is flagged as a rename/move candidate
- C3-3: Items with different paths are not silently merged even when `name` matches

**Synthetic artifacts — write exactly these to `.claude/eval-temp/`:**

Report A — `.claude/eval-temp/2026-01-01T000000-review-skill-foo-bar.md`:

```markdown
---
generated_by: review-skill
schema_version: "1"
date: "2026-01-01T00:00:00"
type: skill
path: skills/foo-bar/SKILL.md
name: foo-bar
summary:
  overall: B
  clarity: B
  completeness: B
  prompt_engineering: B
  context_engineering: B
  goal_alignment: B
  safety: B
  metadata: B
findings: []
---
```

Report B — `.claude/eval-temp/2026-02-01T000000-review-skill-foo-baz.md`:

```markdown
---
generated_by: review-skill
schema_version: "1"
date: "2026-02-01T00:00:00"
type: skill
path: skills/foo-baz/SKILL.md
name: foo-bar
summary:
  overall: B
  clarity: B
  completeness: B
  prompt_engineering: B
  context_engineering: B
  goal_alignment: B
  safety: B
  metadata: B
findings: []
---
```

**Execution:**

1. Write both synthetic reports to `.claude/eval-temp/`
2. Launch an Agent (allowed-tools: Read, Glob, Write, Bash) to run `/review-analytics .claude/eval-temp/`. If the agent does not return or errors out, mark all C3-* criteria as FAIL with note "agent timeout or crash" and proceed.
3. Capture the full output
4. Check each criterion against the output and record PASS/FAIL with a one-sentence excerpt

---

### Case 4: Scaffold Registration Verification

**Sprint contract — plugin mode — acceptance criteria (defined before execution):**

- C4-P1: SKILL.md written under `skills/eval-test-scaffold/` (not `.claude/skills/`)
- C4-P2: README.md updated under a `## Command Families` heading (not `## Skills`, `## File Structure`, or `## Installation`)
- C4-P3: CLAUDE.md updated under `## Commands`

**Sprint contract — maintenance mode — acceptance criteria (defined before execution):**

- C4-M1: SKILL.md written under `.claude/skills/eval-test-scaffold/` (not `skills/`)
- C4-M2: CLAUDE.md updated under `## Commands` only (README.md not modified)

**Execution (plugin mode):**

1. Read the full content of `README.md` and store it as `readme_before`
2. Read the full content of `CLAUDE.md` and store it as `claude_before`
3. Launch an Agent (allowed-tools: Read, Glob, Write, Edit, Bash) to run `/scaffold-skill plugin eval-test-scaffold` and answer "yes" to all confirmation prompts. If the agent does not return or errors out, mark all C4-P* criteria as FAIL with note "agent timeout or crash" and skip to cleanup.
4. Check that `skills/eval-test-scaffold/SKILL.md` exists (C4-P1)
5. Read README.md again; diff against `readme_before` — verify the new entry appears under `## Command Families` (C4-P2)
6. Read CLAUDE.md again; diff against `claude_before` — verify the new entry appears under `## Commands` (C4-P3)
7. Record PASS/FAIL per criterion

**Execution (maintenance mode):**

1. Read the full content of `CLAUDE.md` and store it as `claude_before_maint`
2. Read the full content of `README.md` and store it as `readme_before_maint`
3. Launch an Agent (allowed-tools: Read, Glob, Write, Edit, Bash) to run `/scaffold-skill maintenance eval-test-scaffold-maint` and answer "yes" to all confirmation prompts. If the agent does not return or errors out, mark all C4-M* criteria as FAIL with note "agent timeout or crash" and skip to cleanup.
4. Check that `.claude/skills/eval-test-scaffold-maint/SKILL.md` exists (C4-M1)
5. Read CLAUDE.md again; diff against `claude_before_maint` — verify the new entry appears under `## Commands` (C4-M2)
6. Read README.md again; compare to `readme_before_maint` — confirm no new entries were added (C4-M2 corollary)
7. Record PASS/FAIL per criterion

**Cleanup (run regardless of pass/fail):**

```bash
rm -rf skills/eval-test-scaffold
rm -rf .claude/skills/eval-test-scaffold-maint
```

Then revert any doc changes introduced by the scaffold runs using Edit or by reading the pre-run content and restoring it. If cleanup fails, report the failure and list files that need manual removal.

---

### Case 5: Reliability Pattern Detection

**Sprint contract — acceptance criteria (defined before execution):**

- C5-1: At least one `Impact: High` or `Impact: Medium` finding in the Safety dimension citing missing "failure path" for an external dependency or missing "stop condition" for recursion
- C5-2: At least one `Impact: High` or `Impact: Medium` finding in the Completeness dimension citing missing "chain-level completeness" or failure to propagate `[INCOMPLETE]` / stub-dependency states
- C5-3: At least one `Evidence:` field tied to specific workflow text showing an unchecked dependency call
- C5-4: At least one `Recommended:` block includes a concrete reliability pattern (circuit breaker, progressive fallback, or bounded execution)

**Synthetic artifact — write exactly this content to `.claude/eval-temp/agents/eval-test-reliability-agent.md`:**

```markdown
---
name: eval-test-reliability-agent
description: >
  Processes data by spawning subagents for each data source, fetches external
  content, and persists results. Use for data processing pipelines.
allowed-tools: Agent, WebFetch, Write, Read
---

# Eval Test Reliability Agent

## Workflow

### Step 1: Spawn source agents

Launch three subagents via the Agent tool, one per data source:
- Agent A: fetch data from https://api.source-a.example.com/data
- Agent B: fetch data from https://api.source-b.example.com/data
- Agent C: fetch data from https://api.source-c.example.com/data

Collect all three results.

### Step 2: Fetch supplementary content

Use WebFetch to retrieve https://reference.example.com/catalog for metadata enrichment.

### Step 3: Merge results

Combine the three agent outputs with the WebFetch content into a single merged dataset.

### Step 4: Persist

Write the merged dataset to output/results.json using Write.

### Step 5: Report

Output a summary of the processed records.
```

**Execution:**

1. Write the synthetic artifact above to `.claude/eval-temp/agents/eval-test-reliability-agent.md`
2. Launch an Agent (allowed-tools: Read, Glob, Write, Bash) to run `/review-agent .claude/eval-temp/agents/eval-test-reliability-agent.md`. If the agent does not return or errors out, mark all C5-* criteria as FAIL with note "agent timeout or crash" and proceed to cleanup.
3. Capture the full output
4. Check each criterion against the output and record PASS/FAIL with a one-sentence excerpt

---

## Compaction Checkpoint

After all selected cases have executed, pause and compact context before assembling the final report. Summarize per-case results into a structured intermediate record before proceeding:

```
Case N: [description] — criteria C-1: PASS/FAIL, C-2: PASS/FAIL, ...
```

## Phase 3 — Cleanup and Report

### Step 1: Remove synthetic artifacts

```bash
rm -rf .claude/eval-temp
```

If the directory does not exist (e.g., a case was BLOCKED before writing), note that and continue. If removal fails, report which paths remain and need manual cleanup.

### Step 2: Assemble results report

Present the report with the overall verdict first, then per-case details.

```
## Eval Cases Results — YYYY-MM-DD

## Overall: N/5 cases passed  [CLEAN — safe to commit] or [REGRESSION DETECTED — do not commit until fixed]

| Case | Description                    | Criteria | Passed | Failed | Verdict     |
|------|--------------------------------|----------|--------|--------|-------------|
| 1    | Real Issue Detection           | 4        | N      | N      | PASS / FAIL |
| 2    | Cosmetic Non-Overstatement     | 3        | N      | N      | PASS / FAIL |
| 3    | Analytics Rename/Move          | 3        | N      | N      | PASS / FAIL |
| 4    | Scaffold Registration          | 5        | N      | N      | PASS / FAIL |
| 5    | Reliability Pattern Detection  | 4        | N      | N      | PASS / FAIL |

## Regression Verdict
[CLEAN — safe to commit] or [REGRESSION DETECTED — do not commit until fixed]
```

For each FAIL: show the criterion ID, what was expected, and what the actual output showed (quote or paraphrase the relevant excerpt).

For BLOCKED cases: show which skill was missing and what it would have tested.

### Step 3: Persist

Ask: "Save report to `.claude/reviews/YYYY-MM-DDTHHMMSS-eval-cases.md`? (yes/no)"

If yes, write the report. Use today's date and current time in the filename. If the directory does not exist, create it first.

### Step 4: What's Next

End your response with this menu:

---
**What's next?**
1. Re-run a specific case → `/run-eval-cases <case-number>`
2. Review the review system → `/review-claude-config .`
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke `/run-eval-cases` with the specified case number. **2** → invoke `/review-claude-config .`. **3** → acknowledge and stop.

## Hard Rules

- **Cleanup runs even on failure.** Delete `.claude/eval-temp/` at the end of Phase 3 regardless of case outcomes. If Case 4 cleanup must happen mid-phase, do it immediately after that case's execution.
- **BLOCKED is not FAIL.** If a required skill is missing, mark the case BLOCKED (not FAIL), exclude it from the pass/fail count, and report it separately.
- **Stop conditions.** If a Phase 2 agent fails entirely (not just produces a weak review, but crashes or errors), mark that case FAIL for all criteria, note the agent error, and continue with the next case.
- **Sprint contracts are fixed.** Do not adjust acceptance criteria based on what the review actually produces. Evaluate actual output against the criteria as written.
- **Present all results before asking** about persistence.
- **Case 4 doc revert is mandatory.** Scaffold writes to shared docs (README.md, CLAUDE.md). Always revert those changes after Case 4 verification, even if criteria passed. Record whether revert succeeded.
