---
name: review-skill
description: >
  Evaluate a single Claude Code skill (SKILL.md) across 7 dimensions: Clarity,
  Completeness, Prompt Engineering, Context Engineering, Goal Alignment, Safety,
  and Metadata. Produces a quality certificate with concrete optimization
  recommendations. Use when reviewing an individual skill or when delegated by
  /review-claude-config.
argument-hint: <path-to-SKILL.md>
allowed-tools: Read, Write, Glob, WebSearch, WebFetch
---

# Review Skill

Evaluate a single Claude Code skill for quality across 7 evidence-based dimensions.

## Argument Handling

- `$ARGUMENTS` is the path to a SKILL.md file.
- Validate the file exists and contains YAML frontmatter with a `name` field (required for skills).
- If the file does not look like a skill, report the error and stop.

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
- `references/skill-evaluation-guide.md`

## Phase 2 — Evaluation

### Step A: Goal Inference + Domain Research

1. Read the skill file and infer its primary goal/domain in one sentence.
2. Domain research (follow orchestration flags if in orchestrated mode):
   - If `websearch_available`: perform 1-2 WebSearch queries for domain best practices.
   - If `webfetch_available`: fetch 1-2 most relevant URLs with WebFetch using prompt: "Extract domain best practices, benchmarks, and configuration patterns relevant to [domain]. Max 500 words."
   - If neither available: use model knowledge only.
   - Apply source quality criteria from `references/source-quality-criteria.md`: discard marketing/opinion/outdated content, prefer Tier 1-2 sources, cross-validate claims used in Goal Alignment scoring.
3. Synthesize: what should a high-quality skill in this domain include?

### Step B: Scoring + Recommendations

Score using the rubric as the PRIMARY basis. The skill evaluation guide provides type-specific criteria. Domain research informs Goal Alignment and enriches recommendations but does NOT alter scoring criteria for other dimensions.

**Skill-specific evaluation criteria** (from evaluation guide):
- **Clarity**: Check workflow step sequencing, conditional branch criteria, parallel/sequential markers.
- **Completeness**: Check argument handling, output format, error handling, stop conditions.
- **Prompt Engineering**: Check for structured output templates, role priming, few-shot examples, constraints, CoT guidance.
- **Context Engineering**: Check progressive disclosure, reference file separation, tool set curation, subagent isolation, output conciseness.
- **Goal Alignment**: Check domain knowledge, tool/structure fit, workflow coverage of domain requirements.
- **Safety**: Check least-privilege tools, confirmation gates (if Write/Bash/Edit), stop conditions, `disable-model-invocation` where appropriate.
- **Metadata**: Check frontmatter completeness, description accuracy, tool list matches actual usage, `argument-hint` present.

## Phase 3 — Output

Return the report in this EXACT format:

### Goal
[One sentence describing what this skill aims to achieve]

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | [A-F] | 15% | [One line] |
| Completeness | [A-F] | 15% | [One line] |
| Prompt Engineering | [A-F] | 15% | [One line] |
| Context Engineering | [A-F] | 15% | [One line] |
| Goal Alignment | [A-F] | 20% | [One line] |
| Safety | [A-F] | [10/15%] | [One line] |
| Metadata | [A-F] | [10/5%] | [One line] |
| **Overall** | **[A-F]** | **100%** | **Weighted: XX.X** |

Calculate overall grade:
1. Determine weights: if skill has Write/Bash/Edit in allowed-tools, Safety=15% and Metadata=5%; otherwise Safety=10% and Metadata=10%. All other weights unchanged.
2. Convert grades: A=95, B=85, C=75, D=65, F=50.
3. Weighted score = sum(grade_value × weight) for all 7 dimensions.
4. Map back: ≥90→A, ≥80→B, ≥70→C, ≥60→D, <60→F.
5. Show in Overall Justification: "Weighted: XX.X → [Grade]"

### Grading Boundary Examples

**Clarity B vs C:** B has a clear workflow where step order is unambiguous but one conditional ("if needed") lacks specific criteria. C has steps that two models would sequence differently because dependencies between steps are not explicit.

**Safety B vs C:** B restricts tools to what's needed and includes a confirmation gate before writes. C has tools broader than needed (e.g., Bash when only Read is required) or could modify user files without explicit confirmation.

[If WebSearch was unavailable, add: "Goal Alignment scored without web verification."]

### Strengths
- [strength 1]
- [strength 2]
- [strength 3 if applicable]

### Recommendations

#### 1. [Title] (Impact: [High/Medium/Low], Category: [Workflow|Prompt|Context|Safety|Metadata|Trigger|Output])
**Evidence:** [Quote or summarize the exact text that caused the issue, with path or section reference]

**Why it matters:** [What to change and why, referencing baseline techniques or domain best practices]

**Validation:** [How to confirm the fix on re-review]

**Current:**
```
[existing text from the skill]
```

**Recommended:**
```
[improved text — concrete rewrite]
```

[Repeat for each recommendation, ordered by impact]

#### Reference File Recommendation
[If applicable: flag whether bundled reference files would improve this skill's context engineering. Explain what to extract and why.]

## Phase 4 — Report Persistence (standalone mode only)

In orchestrated mode, skip this phase entirely — return only the structured certificate above.

In standalone mode:
1. Present the certificate to the user.
2. Confirm before writing: "Save review report to `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-review-skill.md`?"
3. If confirmed, assemble report with YAML frontmatter:

```yaml
---
generated_by: review-skill
schema_version: 1
date: YYYY-MM-DD
target: /absolute/path/to/skill
baseline_version: YYYY-MM-DD
items_reviewed: 1
summary:
  - name: skill-name                    # display label; analytics should track by path first
    type: Skill
    path: relative/path/to/SKILL.md
    overall: B
    score: 85.0
    clarity: B
    completeness: A
    prompt_engineering: B
    context_engineering: B
    goal_alignment: B
    safety: A
    metadata: B
---
```

4. Write the report file. Suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report`
5. **What's Next?** (standalone mode only — skip in orchestrated mode)

After all output is complete, end your response with this menu (substitute `<report-path>` with the actual report path from step 4):

---
**What's next?**
1. Apply findings → `/apply-skill-review-findings <report-path>`
2. Review another skill
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke `/apply-skill-review-findings` with the report path. **2** → ask for the skill path, then invoke `/review-skill`. **3** → acknowledge and stop.

## Error Handling

On evaluation failure, return a structured error block:

```
## ERROR
{item_path}: {reason}
```

In orchestrated mode, the orchestrator logs this and continues with remaining items.

## Hard Rules

- **Read-only on the analyzed skill.** Never modify the skill being reviewed. Write only to `.claude/reviews/`.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present the full certificate before any follow-up actions.**
