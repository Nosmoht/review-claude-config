---
name: review-agent
description: >
  Evaluates a single agent .md across 7 dimensions including activation
  precision and trigger coverage. Use when asked to 'review agent' or
  dispatched by /review-claude-config. Do NOT use for skills or rules — use
  /review-skill or /review-rule.
argument-hint: <path-to-agent.md>
allowed-tools: Read, Write, Glob, WebSearch, WebFetch
---

# Review Agent

Evaluate a single Claude Code agent for quality across 7 evidence-based dimensions with agent-specific checks.

## Argument Handling

- `$ARGUMENTS` is the path to an agent .md file.
- Validate the file exists. Agents are single-file, typically in `.claude/agents/` or an `agents/` directory, with optional frontmatter containing `model`, `tools`, `description`, and agent-exclusive fields (`maxTurns`, `background`, `isolation`, `memory`, `initialPrompt`, `mcpServers`, `skills`).
- If the file does not look like an agent (e.g., it's a SKILL.md or rule), report the error and stop.

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

Also load `repo-identification.md` via Glob `**/review-claude-config/references/repo-identification.md` to resolve `suite-root` and `repo-slug`.

**If any of these files is not found, abort with error:** "Required reference not found. Ensure review-claude-config is installed as a sibling skill."

Read the type-specific evaluation guide from this skill's own directory:
- `skills/review-claude-config/references/agent-evaluation-guide.md`

When the agent declares Write, Bash, Edit, or MCP tools in `tools:`/`disallowedTools:`: also read `**/review-claude-config/references/tool-grant-decision-tree.md` for archetype alignment and high-risk combination evaluation (TV-2, TV-3).

## Phase 2 — Evaluation

### Step A: Goal Inference + Domain Research

1. Read the agent file and infer its primary goal/domain in one sentence.
2. Domain research (follow orchestration flags if in orchestrated mode):
   - First, check the domain cache: Read `${CLAUDE_PLUGIN_ROOT}/skills/review-claude-config/references/domain-cache/INDEX.md` and match the agent's domain to a universal cache entry.
   - If `CACHED` (entry exists, ≤90 days old): read the cache file and use as primary domain knowledge. At most 1 supplemental WebSearch query if the cache lacks coverage for this agent's specific area.
   - If `STALE` (≥90 days): perform 1 WebSearch query to refresh.
   - If no cache entry matches: extract domain keywords from the agent's description and content, then perform 1-2 targeted WebSearch queries (technology + workflow + quality aspect, not generic "best practices"). If `webfetch_available`, fetch the most relevant URL.
   - If neither cache nor WebSearch available: use model knowledge only, marked `[no external verification]`.
   - Apply source quality criteria (loaded above or from shared reference materials in orchestrated mode): discard marketing/opinion/outdated content, prefer Tier 1-2 sources, cross-validate claims used in Goal Alignment scoring.
3. Synthesize: what should a high-quality agent in this domain include?

### Step B: Scoring + Recommendations

Score using the rubric as the PRIMARY basis. The agent evaluation guide provides type-specific criteria. Domain research informs Goal Alignment and enriches recommendations but does NOT alter scoring criteria for other dimensions.

**Definition-runtime separation:** When scoring, distinguish definition defects (ambiguous instructions, missing constraints, weak trigger logic) from runtime capability limitations (model cannot perform the task). IRT research (arXiv:2604.00594, ICLR 2026 Workshop) shows these are independent dimensions with heterogeneous failure profiles — conflating them leads to incorrect remediation. A definition defect needs a rewrite; a capability limitation needs a different model or approach.

**Scoring procedure:**

1. Work through the full checklist in `skills/review-claude-config/references/agent-evaluation-guide.md`. Record a PASS, FAIL, or NA verdict for every item in the checklist.
2. **Completeness gate:** Before producing the certificate, verify:
   - Every checklist item has a verdict (no blanks).
   - Every dimension has at least one non-NA item.
   - If any item was not yet evaluated, evaluate it now before continuing.
3. Score each dimension using the rubric, referencing checklist results as evidence. Justification lines in the certificate must cite at least one checklist ID (e.g., "DA-2 FAIL: description matches unrelated requests").
4. The completed checklist is an internal working artifact — do not include it verbatim in the output certificate.

## Phase 3 — Output

Return the report in this EXACT format:

### Goal
[One sentence describing what this agent aims to achieve]

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
1. Determine weights: if agent has Write/Bash/Edit in tools/allowed-tools, Safety=15% and Metadata=5%; otherwise Safety=10% and Metadata=10%. All other weights unchanged.
2. Convert grades: A=95, B=85, C=75, D=65, F=50.
3. Weighted score = sum(grade_value × weight) for all 7 dimensions.
4. Map back: ≥90→A, ≥80→B, ≥70→C, ≥60→D, <60→F.
5. Show in Overall Justification: "Weighted: XX.X → [Grade]"

### Grading Boundary Examples

**Clarity B vs C:** B has a clear workflow where step order is unambiguous but one conditional ("if needed") lacks specific criteria. C has steps that two models would sequence differently because dependencies between steps are not explicit.

**Safety B vs C:** B restricts tools to what's needed and includes a confirmation gate before writes. C has tools broader than needed (e.g., Bash when only Read is required) or could modify user files without explicit confirmation.

**Safety B vs C (agentic):** B addresses all High reliability checks (R1 termination, R4 escalation, R9 safety scope). C is missing any High reliability check — regardless of other Safety criteria.

[If WebSearch was unavailable, add: "Goal Alignment scored without web verification."]

### Strengths
- [strength 1]
- [strength 2]
- [strength 3 if applicable]

### Recommendations

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`. Prefer the `skills/` copy when present; otherwise use the sibling `.claude/skills/` copy. Use that contract's shared recommendation schema below. Keep the agent-specific category vocabulary below.

#### 1. [Title] (Impact: [High/Medium/Low], Category: [Trigger|Examples|Prompt|Context|Safety|Metadata|Model])
**Evidence:** [Quote or summarize the exact text that caused the issue, with path or section reference]

**Why it matters:** [What to change and why, referencing baseline techniques or domain best practices]

**Validation:** [How to confirm the fix on re-review]

**Current:**
```
[existing text from the agent]
```

**Recommended:**
```
[improved text — concrete rewrite]
```

[Repeat for each recommendation, ordered by impact]

#### Reference File Recommendation
[Note: Agents are single-file and cannot have reference files. If the agent would benefit from extracted reference content, recommend converting to a skill instead, explaining the tradeoff.]

## Phase 4 — Report Persistence (standalone mode only)

In orchestrated mode, skip this phase entirely — return only the structured certificate above.

In standalone mode:
1. Present the certificate to the user.
2. Confirm before writing: "Save review report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-agent.md`?"
3. If confirmed, assemble the report using the canonical frontmatter contract located in Step 1 with:
   - `generated_by: review-agent`
   - one `summary` item of type `Agent`
   - `repo: <slug>` and optionally `origin: <git-remote-url>`
   - `type + path` as the canonical identity and `name` as display-only
4. Write the report file. Suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report`
5. **What's Next?** (standalone mode only — skip in orchestrated mode)

After all output is complete, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Apply findings" (Recommended) — description: `"Run /apply-agent-review-findings <report-path> to address High/Medium findings"`
- Option 2 label: "Review another agent" — description: `"Provide an agent path to review next"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Apply findings": invoke `/apply-agent-review-findings` with the report path. On "Review another agent": ask for the agent path, then invoke `/review-agent`. On "Done": acknowledge and stop.

## Error Handling

On evaluation failure, return a structured error block:

```
## ERROR
{item_path}: {reason}
```

In orchestrated mode, the orchestrator logs this and continues with remaining items.

## Hard Rules

- **Read-only on the analyzed agent.** Never modify the agent being reviewed. Write only to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Credential scope (PII/secret redaction).** Before writing content quoted from the analyzed agent to the report path: (1) truncate `evidence` / `current` blocks at 500 characters, (2) redact token-like substrings matching `/[A-Za-z0-9_\-]{20,}/` with `<REDACTED>`, (3) skip writes entirely when the analyzed path matches `**/*.env`, `**/.ssh/**`, or `**/credentials.*` — emit a `{"status": "skipped", "reason": "credential-scope"}` stub instead.
- **Tier A tool justification:** Write + WebSearch/WebFetch are present because: (1) Write is restricted to the `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` directory only — never to the analyzed agent path, never outside this report directory, (2) WebSearch is used only for domain research during Phase 2 Step A goal inference, never for file modification (it is a read-only network tool by Anthropic spec), (3) WebFetch is restricted to fetching documentation URLs identified by WebSearch results during the same domain-research step — used only for evidence gathering on Goal Alignment, never for arbitrary URLs, never for file modification, and bounded to a single fetch per review per the resource caps. Read and Glob are read-only and need no per-tool binding (SP-2b applies to mutating tools only). The read-only Hard Rule above prevents any write-to-analyzed-agent risk; combined with the Write path restriction, this confines all mutations to the report directory allowlist.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present the full certificate before any follow-up actions.**
