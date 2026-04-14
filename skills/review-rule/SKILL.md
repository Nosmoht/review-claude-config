---
name: review-rule
description: >
  Evaluates a single rule .md across 3 dimensions (Clarity, Completeness, Goal
  Alignment). Use when asked to 'review rule' or dispatched by
  /review-claude-config. Do NOT use for skills or agents — use /review-skill or
  /review-agent.
argument-hint: <path-to-rule.md>
allowed-tools: Read, Write, Glob, WebSearch, WebFetch
---

# Review Rule

Evaluate a single Claude Code rule for quality across 3 evidence-based dimensions.

## Argument Handling

- `$ARGUMENTS` is the path to a rule .md file.
- Validate the file exists. Rules are plain Markdown files, typically in `.claude/rules/`, with no standardized frontmatter.
- If the file looks like a skill (has SKILL.md frontmatter with `name`) or agent (has `model`/`tools` frontmatter), report the type mismatch and stop.

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

Attempt a trivial WebSearch (e.g., "Claude Code documentation"). If it fails, set `websearch_available = false`. Goal Alignment will be scored from model knowledge only, marked `[no web verification]`.

Attempt a trivial WebFetch (e.g., fetch "https://docs.anthropic.com"). If it fails, set `webfetch_available = false`.

### Step 1: Load References

Locate the `review-claude-config` skill directory (sibling skill in the same plugin). Read these shared references from it:
- `references/scoring-rubric.md` — the grading criteria
- `references/engineering-baseline.md` — prompt, context, and tool design techniques
- `references/source-quality-criteria.md` — source credibility and filtering criteria for web research

Use Glob to find the files if the path is not immediately known: `**/review-claude-config/references/scoring-rubric.md`

**If any of these files is not found, abort with error:** "Required reference not found. Ensure review-claude-config is installed as a sibling skill."

Read the type-specific evaluation guide from this skill's own directory:
- `references/rule-evaluation-guide.md`

## Phase 2 — Evaluation

### Step A: Goal Inference + Domain Research

1. Read the rule file and infer its primary constraint/goal in one sentence.
2. Domain research (follow orchestration flags if in orchestrated mode):
   - First, check the domain cache: Glob `**/review-claude-config/references/domain-cache/INDEX.md` and match the rule's domain to a universal cache entry.
   - If `CACHED` (entry exists, ≤90 days old): read the cache file and use as primary domain knowledge. At most 1 supplemental WebSearch query if the cache lacks coverage for this rule's specific area.
   - If `STALE` (≥90 days): perform 1 WebSearch query to refresh.
   - If no cache entry matches: extract domain keywords from the rule's content, then perform 1-2 targeted WebSearch queries for domain-specific knowledge. If `webfetch_available`, fetch the most relevant URL.
   - If neither cache nor WebSearch available: use model knowledge only, marked `[no external verification]`.
   - Apply source quality criteria (loaded above or from shared reference materials in orchestrated mode): discard marketing/opinion/outdated content, prefer Tier 1-2 sources, cross-validate claims used in Goal Alignment scoring.
3. Synthesize: what should a high-quality rule in this domain enforce?

### Step B: Scoring + Recommendations

Score using the rubric as the PRIMARY basis. Rules use only 3 dimensions (renormalized to 100%): Clarity 30%, Completeness 30%, Goal Alignment 40%. Skip PE, CE, Safety, Metadata.

**Scoring procedure:**

1. Work through the full checklist in `references/rule-evaluation-guide.md`. Record a PASS, FAIL, or NA verdict for every item (ID CL-1 through GA-5).
2. **Completeness gate:** Before producing the certificate, verify:
   - Every checklist item has a verdict (no blanks).
   - Every dimension has at least one non-NA item.
   - If any item was not yet evaluated, evaluate it now before continuing.
3. Score each dimension using the rubric, referencing checklist results as evidence. Justification lines in the certificate must cite at least one checklist ID (e.g., "CL-4 FAIL: uses 'should' instead of 'must'").
4. The completed checklist is an internal working artifact — do not include it verbatim in the output certificate.

## Phase 3 — Output

Return the report in this EXACT format:

### Goal
[One sentence describing what this rule aims to enforce]

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | [A-F] | 30% | [One line] |
| Completeness | [A-F] | 30% | [One line] |
| Goal Alignment | [A-F] | 40% | [One line] |
| **Overall** | **[A-F]** | **100%** | **Weighted: XX.X** |

Calculate overall grade:
1. Convert grades: A=95, B=85, C=75, D=65, F=50.
2. Weighted score = Clarity×.30 + Completeness×.30 + GoalAlignment×.40.
3. Map back: ≥90→A, ≥80→B, ≥70→C, ≥60→D, <60→F.
4. Show in Overall Justification: "Weighted: XX.X → [Grade]"

### Grading Boundary Examples

**Clarity B vs C:** B defines a clear constraint with explicit scope but one term ("appropriate") could be interpreted differently. C has ambiguous scope — two models would apply the rule to different sets of files or operations.

**Completeness B vs C:** B covers the main constraint with defined exceptions but misses one edge case. C covers only the happy path — common edge cases (e.g., monorepo layouts, CI environments) would cause undefined behavior.

[If WebSearch was unavailable, add: "Goal Alignment scored without web verification."]

### Strengths
- [strength 1]
- [strength 2]
- [strength 3 if applicable]

### Recommendations

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`. Prefer the `skills/` copy when present; otherwise use the sibling `.claude/skills/` copy. Use that contract's shared recommendation schema below. Keep the rule-specific category vocabulary below.

#### 1. [Title] (Impact: [High/Medium/Low], Category: [Scope|Clarity|Completeness|Alignment|Exceptions])
**Evidence:** [Quote or summarize the exact text that caused the issue, with path or section reference]

**Why it matters:** [What to change and why, referencing domain best practices]

**Validation:** [How to confirm the fix on re-review]

**Current:**
```
[existing text from the rule]
```

**Recommended:**
```
[improved text — concrete rewrite]
```

[Repeat for each recommendation, ordered by impact]

## Phase 4 — Report Persistence (standalone mode only)

In orchestrated mode, skip this phase entirely — return only the structured certificate above.

In standalone mode:
1. Present the certificate to the user.
2. Confirm before writing: "Save review report to `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-review-rule.md`?"
3. If confirmed, assemble the report using the canonical frontmatter contract located in Step 1 with:
   - `generated_by: review-rule`
   - one `summary` item of type `Rule`
   - non-applicable dimensions set to `null`
   - `type + path` as the canonical identity and `name` as display-only
4. Write the report file. Suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report`
5. **What's Next?** (standalone mode only — skip in orchestrated mode)

After all output is complete, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Apply findings" (Recommended) — description: `"Run /apply-rule-review-findings <report-path> to address High/Medium findings"`
- Option 2 label: "Review another rule" — description: `"Provide a rule path to review next"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Apply findings": invoke `/apply-rule-review-findings` with the report path. On "Review another rule": ask for the rule path, then invoke `/review-rule`. On "Done": acknowledge and stop.

## Error Handling

On evaluation failure, return a structured error block:

```
## ERROR
{item_path}: {reason}
```

In orchestrated mode, the orchestrator logs this and continues with remaining items.

## Hard Rules

- **Read-only on the analyzed rule.** Never modify the rule being reviewed. Write only to `.claude/reviews/`.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present the full certificate before any follow-up actions.**
- **Use only 3 dimensions.** Never score rules on PE, CE, Safety, or Metadata.
