---
name: review-hook
description: >
  Evaluates a hooks.json entry + Python script across 5 dimensions (Clarity,
  Completeness, Goal Alignment, Safety, Metadata). Use when asked to 'review
  hook' or after /develop-hooks. Do NOT use for skills or agents.
argument-hint: <path-to-hooks.json or path-to-hook-script.py>
allowed-tools: Read, Write, Glob, WebSearch, WebFetch
---

# Review Hook

Evaluate a Claude Code hook for quality across 5 evidence-based dimensions.

## Argument Handling

- `$ARGUMENTS` is a path to either a `hooks.json` file or a Python hook script (`.py`).
- If given a `.py` file, locate the associated `hooks.json` in the same directory.
- If given a `hooks.json`, identify all Python scripts referenced by it and read them.
- If neither file is found, report the error and stop.
- A "hook unit" is a `hooks.json` entry plus all referenced Python scripts. Evaluate as a unit.

## Mode Detection

Check whether the prompt contains an orchestration metadata block:

```
---orchestration---
mode: orchestrated
websearch_available: true|false
webfetch_available: true|false
domain_cache: |
  <cached domain content or "none">
---
```

- If present → **orchestrated mode** (skip tool checks, use provided flags and cache, return structured certificate only, no user interaction).
- If absent → **standalone mode** (full workflow below).

## Phase 1 — Setup (standalone mode only)

### Step 0: Tool Availability Checks

Attempt a trivial WebSearch (e.g., "Claude Code hook documentation"). If it fails, set `websearch_available = false`. Goal Alignment will be scored from model knowledge only, marked `[no web verification]`.

Attempt a trivial WebFetch. If it fails, set `webfetch_available = false`.

### Step 1: Load References

Locate the `review-claude-config` skill directory. Read these shared references:
- `references/scoring-rubric.md` — the grading criteria
- `references/engineering-baseline.md` — prompt, context, and tool design techniques
- `references/source-quality-criteria.md` — source credibility and filtering criteria

Use Glob to find the files if the path is not immediately known: `**/review-claude-config/references/scoring-rubric.md`

**If any of these files is not found, abort with error:** "Required reference not found. Ensure review-claude-config is installed as a sibling skill."

Read the type-specific evaluation guide from this skill's own directory:
- `references/hook-evaluation-guide.md`

## Phase 2 — Evaluation

### Step A: Hook Purpose Inference

1. Read `hooks.json` and all referenced Python scripts.
2. Identify: event type(s), matcher scope (if any), and stated purpose from the `description` field or filename.
3. State the hook's purpose in one sentence: "This hook [does X] when [event Y] fires [on Z]."

### Step B: Domain Research

Check the domain cache for `hooks-quality`:
- If `CACHED` (≤90 days): use cache as primary knowledge.
- If `STALE` or `MISS`: perform 1 WebSearch for Claude Code hook best practices. Fetch the top result if `webfetch_available`.
- If unavailable: use model knowledge only, marked `[no external verification]`.

Apply source quality criteria: prefer official Anthropic docs (Tier 1) and production case studies (Tier 2).

### Step C: Scoring

Score using the rubric and the hook-evaluation-guide checklist. Hooks use 5 dimensions:

| Dimension | Weight |
|-----------|--------|
| Clarity | 20% |
| Completeness | 20% |
| Goal Alignment | 25% |
| Safety | 25% |
| Metadata | 10% |

**Scoring procedure:**

1. Work through the full checklist in `references/hook-evaluation-guide.md`. Record PASS, FAIL, or NA for every item (HC-1 through GA-3).
2. **Completeness gate:** Every checklist item must have a verdict. Every dimension must have at least one non-NA item.
3. Score each dimension using the rubric, citing at least one checklist ID per justification (e.g., "PY-3 FAIL: exit 0 used instead of exit 1 for block decision").
4. The completed checklist is an internal working artifact — do not include it verbatim in the output.

## Phase 3 — Output

Return the report in this EXACT format:

### Goal
[One sentence: "This hook [does X] when [event Y] fires [on Z]"]

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | [A-F] | 20% | [One line] |
| Completeness | [A-F] | 20% | [One line] |
| Goal Alignment | [A-F] | 25% | [One line] |
| Safety | [A-F] | 25% | [One line] |
| Metadata | [A-F] | 10% | [One line] |
| **Overall** | **[A-F]** | **100%** | **Weighted: XX.X** |

Calculate overall grade:
1. Convert grades: A=95, B=85, C=75, D=65, F=50.
2. Weighted score = Clarity×.20 + Completeness×.20 + GoalAlignment×.25 + Safety×.25 + Metadata×.10.
3. Map back: ≥90→A, ≥80→B, ≥70→C, ≥60→D, <60→F.
4. Show in Overall Justification: "Weighted: XX.X → [Grade]"

### Grading Boundary Examples

**Safety B vs C:** B validates all exit codes correctly and has a top-level exception handler. C uses exit 0 for blocking decisions, or has one unguarded exception path that could crash the hook silently.

**Goal Alignment B vs C:** B fires at the correct lifecycle event and its matcher is appropriately scoped. C fires at the right event but the matcher is too broad (e.g., matches all Edit operations when only SKILL.md edits are intended).

[If WebSearch was unavailable, add: "Goal Alignment scored without web verification."]

### Strengths
- [strength 1]
- [strength 2]
- [strength 3 if applicable]

### Recommendations

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`. Use that contract's shared recommendation schema.

#### 1. [Title] (Impact: [High/Medium/Low], Category: [Event|Matcher|ExitCode|Safety|Performance|Metadata])
**Evidence:** [Quote or summarize the exact text/code that caused the issue, with file and line reference]

**Why it matters:** [What to change and why]

**Validation:** [How to confirm the fix on re-review]

**Current:**
```
[existing code or config]
```

**Recommended:**
```
[improved version — concrete rewrite]
```

[Repeat for each recommendation, ordered by impact]

## Phase 4 — Report Persistence (standalone mode only)

In orchestrated mode, skip this phase entirely — return only the structured certificate above.

In standalone mode:
1. Present the certificate to the user.
2. Confirm before writing: "Save review report to `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-review-hook.md`?"
3. If confirmed, assemble the report using the canonical frontmatter contract with:
   - `generated_by: review-hook`
   - one `summary` item of type `Hook`
   - non-applicable dimensions (PE, CE) set to `null`
   - `type + path` as the canonical identity and `name` as display-only
4. Write the report file. Suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report`
5. **What's Next?**

After all output is complete, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Apply findings" (Recommended) — description: `"Run /apply-hook-findings <report-path> to address High/Medium findings"`
- Option 2 label: "Review another hook" — description: `"Provide a hook path to review next"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Apply findings": invoke `/apply-hook-findings` with the report path. On "Review another hook": ask for the hook path, then invoke `/review-hook`. On "Done": acknowledge and stop.

## Error Handling

On evaluation failure, return a structured error block:

```
## ERROR
{item_path}: {reason}
```

In orchestrated mode, the orchestrator logs this and continues with remaining items.

## Hard Rules

- **Read-only on the analyzed hook files.** Never modify hooks.json or Python scripts being reviewed. Write only to `.claude/reviews/`.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite.**
- **Present the full certificate before any follow-up actions.**
- **Evaluate the full hook unit** (hooks.json entry + all referenced scripts). Do not score hooks.json alone.
