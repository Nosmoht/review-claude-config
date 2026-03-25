---
name: review-rule
description: >
  Evaluate a single Claude Code rule (.md file) across 3 dimensions: Clarity (30%),
  Completeness (30%), and Goal Alignment (40%). Rules are directives without tools
  or frontmatter, so Prompt Engineering, Context Engineering, Safety, and Metadata
  do not apply. Produces a quality certificate with concrete optimization
  recommendations. Use when reviewing an individual rule or when delegated by
  /review-claude-config.
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

Use Glob to find the files if the path is not immediately known: `**/review-claude-config/references/scoring-rubric.md`

**If either file is not found, abort with error:** "Required reference not found. Ensure review-claude-config is installed as a sibling skill."

Read the type-specific evaluation guide from this skill's own directory:
- `references/rule-evaluation-guide.md`

## Phase 2 — Evaluation

### Step A: Goal Inference + Domain Research

1. Read the rule file and infer its primary constraint/goal in one sentence.
2. Domain research (follow orchestration flags if in orchestrated mode):
   - If `websearch_available`: perform 1-2 WebSearch queries for domain best practices related to the rule's constraint.
   - If `webfetch_available`: fetch 1-2 most relevant URLs with WebFetch using prompt: "Extract domain best practices, benchmarks, and configuration patterns relevant to [domain]. Max 500 words."
   - If neither available: use model knowledge only.
3. Synthesize: what should a high-quality rule in this domain enforce?

### Step B: Scoring + Recommendations

Score using the rubric as the PRIMARY basis. Rules use only 3 dimensions (renormalized to 100%):

- **Clarity (30%)**: Is the rule unambiguous? Could two models interpret it differently? Are terms precise? Is scope explicit?
- **Completeness (30%)**: Are edge cases and exceptions addressed? Are scope boundaries defined? Are rule interactions considered?
- **Goal Alignment (40%)**: Does the rule achieve its stated constraint? Is it proportional? Does domain knowledge reveal missing constraints?

Skip: Prompt Engineering, Context Engineering, Safety, Metadata — these do not apply to rules (no tools, no frontmatter, directives not prompts).

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

#### 1. [Title] (Impact: [High/Medium/Low])
[What to change and why, referencing domain best practices]

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
3. If confirmed, assemble report with YAML frontmatter:

```yaml
---
generated_by: review-rule
schema_version: 1
date: YYYY-MM-DD
target: /absolute/path/to/rule
baseline_version: YYYY-MM-DD
items_reviewed: 1
summary:
  - name: rule-name
    type: Rule
    path: relative/path/to/rule.md
    overall: B
    score: 85.0
    clarity: B
    completeness: A
    prompt_engineering: null
    context_engineering: null
    goal_alignment: B
    safety: null
    metadata: null
---
```

4. Write the report file. Suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report`
5. Suggest next steps:
   - "To automatically apply High/Medium findings: `/apply-rule-review-findings <report-path>`"
   - "To apply changes manually, use the Current/Recommended blocks in each recommendation as a guide."

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
- **Every recommendation must include a concrete rewrite** — not just "improve X."
- **Present the full certificate before any follow-up actions.**
- **Use only 3 dimensions.** Never score rules on PE, CE, Safety, or Metadata.
