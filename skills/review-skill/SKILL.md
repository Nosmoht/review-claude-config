---
name: review-skill
description: >
  Evaluates a single SKILL.md across 7 quality dimensions and produces an
  optimization certificate. Use when asked to 'review skill' or dispatched by
  /review-claude-config. Do NOT use for agents or rules — use /review-agent or
  /review-rule.
argument-hint: <path-to-SKILL.md>
allowed-tools: Read, Write, Glob, WebSearch, WebFetch
---

# Review Skill

Evaluate a single Claude Code skill for quality across 7 evidence-based dimensions.

## Argument Handling

- `$ARGUMENTS` is the path to a SKILL.md file.
- If `$ARGUMENTS` is empty, prompt the user: "Provide the path to a SKILL.md file to review." and stop.
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
- `references/source-quality-criteria.md` — source credibility and filtering criteria for web research

Use Glob to find the files if the path is not immediately known: `**/review-claude-config/references/scoring-rubric.md`

**If any of these files is not found, abort with error:** "Required reference not found. Ensure review-claude-config is installed as a sibling skill."

Read the type-specific evaluation guide from this skill's own directory:
- `references/skill-evaluation-guide.md`

When the skill declares Write, Bash, Edit, or MCP tools in `allowed-tools`: also read `**/review-claude-config/references/tool-grant-decision-tree.md` for archetype alignment and high-risk combination evaluation (SP-2, SP-4).

## Phase 2 — Evaluation

### Step A: Goal Inference + Domain Research

1. Read the skill file and infer its primary goal/domain in one sentence.
2. Domain research (follow orchestration flags if in orchestrated mode):
   - First, check the domain cache: Glob `**/review-claude-config/references/domain-cache/INDEX.md` and match the skill's domain to a universal cache entry.
   - If `CACHED` (entry exists, ≤90 days old): read the cache file and use as primary domain knowledge. At most 1 supplemental WebSearch query if the cache lacks coverage for this skill's specific area.
   - If `STALE` (≥90 days): perform 1 WebSearch query to refresh.
   - If no cache entry matches: extract domain keywords from the skill's description and content, then perform 1-2 targeted WebSearch queries (technology + workflow + quality aspect, not generic "best practices"). If `webfetch_available`, fetch the most relevant URL.
   - If neither cache nor WebSearch available: use model knowledge only, marked `[no external verification]`.
   - Apply source quality criteria (loaded above or from shared reference materials in orchestrated mode): discard marketing/opinion/outdated content, prefer Tier 1-2 sources, cross-validate claims used in Goal Alignment scoring.
3. Synthesize: what should a high-quality skill in this domain include?

**Resource caps (hard limits per review):** ≤3 WebSearch queries, ≤1 WebFetch call, ≤10 reference file reads. Exceeding these indicates scope creep — narrow the research focus rather than broadening.

### Step B: Scoring + Recommendations

Score using the rubric as the PRIMARY basis. The skill evaluation guide provides type-specific criteria. Domain research informs Goal Alignment and enriches recommendations but does NOT alter scoring criteria for other dimensions.

**Scoring procedure:**

1. Work through the full checklist in `references/skill-evaluation-guide.md`. Record a PASS, FAIL, or NA verdict for every item (ID PD-1 through RT-3). RD-1 through RD-6 are reliability diagnostic checks — their FAILs are surfaced in the `### Reliability Diagnostics` output section and contribute to the mapped dimension grade (RD-1/2/3 → Metadata; RD-4 → Completeness; RD-5 → Clarity; RD-6 → Safety). For RD-3, Glob for sibling `SKILL.md` files in the same plugin directory and compare trigger phrases.
2. **Completeness gate:** Before producing the certificate, verify:
   - Every checklist item has a verdict (no blanks).
   - Every dimension has at least one non-NA item.
   - If any item was not yet evaluated, evaluate it now before continuing.
3. Score each dimension using the rubric, referencing checklist results as evidence. Justification lines in the certificate must cite at least one checklist ID (e.g., "WS-2 FAIL: conditionals use 'if needed' without criteria").
4. The completed checklist is an internal working artifact — do not include it verbatim in the output certificate.

## Phase 3 — Output

Return the report in this EXACT format:

### Status
[success | partial | failure]
- `success` — review completed, all grades B or above
- `partial` — review completed, one or more grades C or below
- `failure` — review could not complete (missing file, missing references)

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

**Safety B vs C (agentic skills):** B addresses all High reliability checks (R1 termination, R4 escalation, R9 safety scope). C is missing any High reliability check — regardless of other Safety criteria.

[If WebSearch was unavailable, add: "Goal Alignment scored without web verification."]

### Strengths
- [strength 1]
- [strength 2]
- [strength 3 if applicable]

### Reliability Diagnostics

#### Activation
[For each RD-1/2/3 FAIL: "- **RD-N FAIL**: [evidence quote or reference] → Fix: [specific action]"]
[If all RD-1/2/3 PASS: "No activation issues detected."]

#### Execution
[For each RD-4/5/6 FAIL: "- **RD-N FAIL**: [evidence quote or reference] → Fix: [specific action]"]
[If all RD-4/5/6 PASS: "No execution issues detected."]

### Recommendations

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`. Prefer the `skills/` copy when present; otherwise use the sibling `.claude/skills/` copy. Use that contract's shared recommendation schema below. Keep the skill-specific category vocabulary below.

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
3. If confirmed, assemble the report using the canonical frontmatter contract located in Step 1 with:
   - `generated_by: review-skill`
   - one `summary` item of type `Skill`
   - `type + path` as the canonical identity and `name` as display-only
4. Write the report file. Suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report`
5. **What's Next?** (standalone mode only — skip in orchestrated mode)

After all output is complete, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Apply findings" (Recommended) — description: `"Run /apply-skill-review-findings <report-path> to address High/Medium findings"`
- Option 2 label: "Review another skill" — description: `"Provide a skill path to review next"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Apply findings": invoke `/apply-skill-review-findings` with the report path. On "Review another skill": ask for the skill path, then invoke `/review-skill`. On "Done": acknowledge and stop.

## Error Handling

On evaluation failure, return a structured error block:

```
## ERROR
{item_path}: {reason}
```

In orchestrated mode, the orchestrator logs this and continues with remaining items.

## Hard Rules

- **Read-only on the analyzed skill.** Never modify the skill being reviewed. Write only to `.claude/reviews/`.
- **Tier A tool justification:** Write+WebSearch/WebFetch are present because: (1) Write is restricted to `.claude/reviews/` for report persistence only, (2) WebSearch/WebFetch are for domain research, not file modification, (3) read-only Hard Rule above prevents write-to-analyzed-file risk.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present the full certificate before any follow-up actions.**
