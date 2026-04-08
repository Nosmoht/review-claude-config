---
name: review-claude-md
description: >
  Evaluates a CLAUDE.md file across 4 dimensions (Clarity, Completeness,
  Context Engineering, Goal Alignment). Use when asked to 'review CLAUDE.md'
  or after /audit-repo flags a missing or low-quality CLAUDE.md. Do NOT use
  for skills, agents, or rules — use /review-skill, /review-agent, or /review-rule.
argument-hint: <path-to-CLAUDE.md>
allowed-tools: Read, Write, Glob, WebSearch, WebFetch
---

# Review Claude MD

Evaluate a CLAUDE.md file for quality across 4 evidence-based dimensions.

## Argument Handling

- `$ARGUMENTS` is the path to a CLAUDE.md file.
- Validate the file exists. CLAUDE.md files are plain Markdown with no required frontmatter.
- If the path resolves to a SKILL.md or an agent/rule file, report the type mismatch and stop.
- If `$ARGUMENTS` is empty, look for CLAUDE.md in the current working directory.

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

Attempt a trivial WebSearch (e.g., "Claude Code CLAUDE.md documentation"). If it fails, set `websearch_available = false`. Goal Alignment will be scored from model knowledge only, marked `[no web verification]`.

Attempt a trivial WebFetch. If it fails, set `webfetch_available = false`.

### Step 1: Load References

Locate the `review-claude-config` skill directory (sibling skill in the same plugin). Read these shared references from it:
- `references/scoring-rubric.md` — the grading criteria
- `references/engineering-baseline.md` — prompt, context, and tool design techniques
- `references/source-quality-criteria.md` — source credibility and filtering criteria for web research

Use Glob to find the files if the path is not immediately known: `**/review-claude-config/references/scoring-rubric.md`

**If any of these files is not found, abort with error:** "Required reference not found. Ensure review-claude-config is installed as a sibling skill."

Read the type-specific evaluation guide from this skill's own directory:
- `references/claude-md-evaluation-guide.md`

## Phase 2 — Evaluation

### Step A: Context Inference + Domain Research

1. Read the CLAUDE.md file and identify:
   - Project type (e.g., Kubernetes infrastructure, Python service, TypeScript app)
   - Stated purpose and audience
   - Which sections are present (Architecture, Commands, Working Guidelines, Development Conventions, etc.)
2. Domain research (follow orchestration flags if in orchestrated mode):
   - Check the domain cache: Glob `**/review-claude-config/references/domain-cache/INDEX.md` and match the project type.
   - If `CACHED` (≤90 days): read the cache file as primary domain knowledge.
   - If `STALE` or `MISS`: perform 1 WebSearch using "Claude Code CLAUDE.md best practices [project-type]" where [project-type] is the one-word project type identified in step 1 (e.g., "Kubernetes", "Python service", "TypeScript app"). Fetch the top result if `webfetch_available`.
   - If unavailable: use model knowledge only, marked `[no external verification]`.
   - Apply source quality criteria: prefer official Anthropic docs (Tier 1).
3. Synthesize: what should a high-quality CLAUDE.md for this project type include?

### Step B: Command Inventory Verification

For every command listed in the CLAUDE.md:
1. Classify the command:
   - **Slash command** (`/name`): resolve to `skills/name/SKILL.md` first,
     then `.claude/skills/name/SKILL.md` as fallback.
   - **Shell command** (`make`, `pytest`, `git`, `gh`, `uv`): mark as
     SHELL — no file resolution; skip Glob check.
   - **Inline path** (explicit file path): verify the path exists directly.
2. For slash commands, use Glob to verify the resolved path exists.
3. Mark each command as **VERIFIED** (file found), **STALE** (file not found
   or path mismatch), or **SHELL** (non-resolvable shell command, not checked).

Record the verification results — they are required evidence for Goal Alignment scoring.

### Step C: Scoring

Score using the rubric as the PRIMARY basis. CLAUDE.md files use 4 dimensions:

| Dimension | Weight |
|-----------|--------|
| Clarity | 25% |
| Completeness | 25% |
| Context Engineering | 25% |
| Goal Alignment | 25% |

**Scoring procedure:**

1. Work through the full checklist in `references/claude-md-evaluation-guide.md`. Record PASS, FAIL, or NA for every item (CL-1 through GA-6).
2. **Completeness gate:** Every checklist item must have a verdict. Every dimension must have at least one non-NA item.
3. Score each dimension using the rubric, citing at least one checklist ID per justification line (e.g., "CI-3 FAIL: 4 of 7 listed commands resolve to missing files").
4. The completed checklist is an internal working artifact — do not include it verbatim in the output.

## Phase 3 — Output

Return the report in this EXACT format:

### Goal
[One sentence describing the project this CLAUDE.md governs and what it aims to achieve for Claude Code sessions]

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | [A-F] | 25% | [One line] |
| Completeness | [A-F] | 25% | [One line] |
| Context Engineering | [A-F] | 25% | [One line] |
| Goal Alignment | [A-F] | 25% | [One line] |
| **Overall** | **[A-F]** | **100%** | **Weighted: XX.X** |

Calculate overall grade:
1. Convert grades: A=95, B=85, C=75, D=65, F=50.
2. Weighted score = Clarity×.25 + Completeness×.25 + ContextEngineering×.25 + GoalAlignment×.25.
3. Map back: ≥90→A, ≥80→B, ≥70→C, ≥60→D, <60→F.
4. Show in Overall Justification: "Weighted: XX.X → [Grade]"

### Grading Boundary Examples

**Clarity B vs C:** B has explicit, actionable instructions throughout with one conditional phrased as "should" instead of "must". C contains multiple aspirational statements ("prefer X", "try to Y") that two models would interpret differently.

**Context Engineering B vs C:** B is dense and well-scoped with one section that restates information already derivable from project files. C has noticeable repetition across sections or includes boilerplate that adds tokens without behavioral signal.

**Goal Alignment B vs C:** B's command inventory is fully verified and freshness markers are present, but one path reference is slightly stale. C has 2+ listed commands that resolve to missing files, or omits a major project component that would cause Claude to miss it entirely.

[If WebSearch was unavailable, add: "Goal Alignment scored without web verification."]

### Command Inventory Report

List the verification results from Step B:

| Command | Expected Path | Status |
|---------|--------------|--------|
| `/example` | `skills/example/SKILL.md` | VERIFIED / STALE |

[If all commands verified: "All N commands verified." If stale entries exist: "N of M commands resolve to missing files — see Recommendations."]

### Strengths
- [strength 1]
- [strength 2]
- [strength 3 if applicable]

### Recommendations

Use the recommendation schema below directly (the contract is referenced in shared references loaded in Phase 1 if needed). Keep the CLAUDE.md-specific category vocabulary below.

#### 1. [Title] (Impact: [High/Medium/Low], Category: [Structure|CommandInventory|InstructionQuality|TokenEfficiency|Completeness|Freshness])
**Evidence:** [Quote or summarize the exact text that caused the issue, with section reference]

**Why it matters:** [What to change and why, referencing domain best practices or baseline techniques]

**Validation:** [How to confirm the fix on re-review]

**Current:**
```
[existing text from the CLAUDE.md]
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
2. Confirm before writing: "Save review report to `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-review-claude-md.md`?"
3. If confirmed, assemble the report using the canonical frontmatter contract located in Step 1 with:
   - `generated_by: review-claude-md`
   - one `summary` item of type `ClaudeMd`
   - non-applicable dimensions (PE, CE replaced by ContextEngineering, Safety, Metadata) set to `null`
   - `type + path` as the canonical identity and `name` as display-only
4. Write the report file. Suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report`
5. **What's Next?**

After all output is complete, end your response with this menu (substitute `<report-path>` with the actual report path from step 3):

---
**What's next?**
1. Apply findings → `/apply-claude-md-review-findings <report-path>`
2. Review another CLAUDE.md
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke `/apply-claude-md-review-findings` with the report path. **2** → ask for the file path, then invoke `/review-claude-md`. **3** → acknowledge and stop.

## Error Handling

On evaluation failure, return a structured error block:

```
## ERROR
{item_path}: {reason}
```

In orchestrated mode, the orchestrator logs this and continues with remaining items.

## Hard Rules

- **Read-only on the analyzed CLAUDE.md.** Never modify the file being reviewed. Write only to `.claude/reviews/`.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present the full certificate before any follow-up actions.**
- **Run Command Inventory Verification for every command listed** — never skip this step.
- **Use only 4 dimensions.** Never score CLAUDE.md on Safety or Metadata — those dimensions apply to executable skills/agents, not configuration documents.
