---
name: review-skill
description: >
  Evaluates a single SKILL.md across 7 quality dimensions and produces an
  optimization certificate. Use when asked to 'review skill' or dispatched by
  /review-claude-config. Do NOT use for agents or rules — use /review-agent or
  /review-rule.
argument-hint: <path-to-SKILL.md>
allowed-tools: Read, Write, Glob, WebSearch, WebFetch, Agent, Bash
frozen_from: "894b30cb8e0d4e7d9107c85a8d3361cb5d325675 @ 2026-04-21"
frozen_reason: "pinned for TestEndToEndFixtures assertions"
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

- If present → **orchestrated mode** (single-perspective, legacy): skip tool checks, use provided flags and cache, return structured certificate only, no user interaction. Skip Phase 2b multi-perspective dispatch.
- If absent → **standalone mode** (full workflow below). Default dispatch is **multi-perspective** (3 sibling Agent tool calls) per Phase 2b. User flag `--deep` forces Opus-tier escalation upfront; `--single-perspective` reverts to legacy.

## Phase 1 — Setup (standalone mode only)

### Step 0: Tool Availability Checks

Attempt a trivial WebSearch (e.g., "Claude Code documentation"). If it fails, set `websearch_available = false`. Goal Alignment will be scored from model knowledge only, marked `[no web verification]`.

Attempt a trivial WebFetch (e.g., fetch "https://docs.anthropic.com"). If it fails, set `webfetch_available = false`.

Attempt a trivial Bash probe: `Bash("echo ok")`. If it fails, set `bash_available = false`. In standalone mode when `bash_available = false`: skip b.5 and b.6 (merge + escalation scripts); emit the three unmerged perspective certificates directly in the Phase 3 output and include `degraded_mode: true, missing_perspectives: ["merge-script-unavailable"]`. This applies even when all three perspective calls succeed, because without merge there is no owner-weighted dimension grade.

### Step 1: Load References

Locate the `review-claude-config` skill directory (sibling skill in the same plugin). Read these shared references from it:
- `references/scoring-rubric.md` — the grading criteria
- `references/engineering-baseline.md` — prompt, context, and tool design techniques
- `references/source-quality-criteria.md` — source credibility and filtering criteria for web research

Use Glob to find the files if the path is not immediately known: `**/review-claude-config/references/scoring-rubric.md`

Also load `repo-identification.md` via Glob `**/review-claude-config/references/repo-identification.md` to resolve `suite-root` and `repo-slug`.

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

### Step B — Scoring + Recommendations (legacy / orchestrated mode + `--single-perspective`)

Applied when `mode: orchestrated` OR user passed `--single-perspective` flag.

Score using the rubric as the PRIMARY basis. The skill evaluation guide provides type-specific criteria. Domain research informs Goal Alignment and enriches recommendations but does NOT alter scoring criteria for other dimensions.

**Scoring procedure:**

1. Work through the full checklist in `references/skill-evaluation-guide.md`. Record a PASS, FAIL, or NA verdict for every item (ID PD-1 through IJ-1). RD-1 through RD-6 are reliability diagnostic checks — their FAILs are surfaced in the `### Reliability Diagnostics` output section and contribute to the mapped dimension grade (RD-1/2/3 → Metadata; RD-4 → Completeness; RD-5 → Clarity; RD-6 → Safety). For RD-3, Glob for sibling `SKILL.md` files in the same plugin directory and compare trigger phrases.
2. **Completeness gate — success condition.** Review is complete when ALL of the following hold (binary, not judgement-based):
   - Every checklist item (PD-1 through IJ-1) has a PASS/FAIL/NA verdict. Count verdicts; if `verdict_count != expected_count`, list the missing item IDs explicitly and evaluate each before proceeding. Do not advance until `verdict_count == expected_count`.
   - Every dimension has at least one non-NA item with a cited checklist ID.
   - The certificate table in Phase 3 has exactly 7 dimension rows plus Overall.
   - Every High or Medium finding carries non-empty `Evidence`, `Why it matters`, and `Validation` blocks.
3. Score each dimension using the rubric, referencing checklist results as evidence. Justification lines in the certificate must cite at least one checklist ID (e.g., "WS-2 FAIL: conditionals use 'if needed' without criteria").
4. **Self-check before emit.** Recompute the weighted score (grade-value × weight per dimension, summed). Verify the weights sum to exactly 100%. Verify the row count equals 7 dimensions + Overall. Verify every High/Medium finding has non-empty Evidence and Validation. If any check fails, correct the certificate before emitting.
5. The completed checklist is an internal working artifact — do not include it verbatim in the output certificate.

### Step B-multi — Multi-Perspective Dispatch (standalone mode default)

Applied when standalone AND user did NOT pass `--single-perspective`.

Load `references/perspective-dispatch-protocol.md` and `references/merge-rules.md` JIT. Those files contain the authoritative recipe; the sub-steps below are the orchestration sequence.

**Context budget / masking strategy.** The multi-perspective dispatch produces ≥ 15 tool-call turns (3 Agent calls + up to 10 reference Reads + 2 Bash invocations + 3 Writes). Masking is achieved by **non-re-retrieval via disk-based handoff**: intermediate perspective certificates (≤ 4 K tokens each) are written to disk in b.4 and thereafter referenced only by path. The merge in b.5 consumes `merged.json` produced by a deterministic script, not the raw perspective output in the conversation history. No LLM summarisation step is used, so no summarisation justification is required per CE-X.

**b.1 — Build shared prefix + per-type block + per-perspective suffixes.**

- Block 1 (shared prefix, byte-identical across all 3 perspectives): concatenate `scoring-rubric.md` + `engineering-baseline.md` + `source-quality-criteria.md` + the shared perspective wrapper sentence. ~6,100 Opus-4.7 tokens. Mark `cache_control` on this block.
- Block 2 (per-type block, byte-identical across 3 perspectives for skill review): `skill-evaluation-guide.md` + `boundary-exemplars.md`. ~1,850 tokens. Mark `cache_control`.
- Block 3 (per-perspective, differs per sibling): functional role + ownership contract + output-schema reminder from the matching agent's SKILL frontmatter + body top. ~400 tokens each. Mark `cache_control`.
- Block 4 (artifact, uncached): `## Item Under Review\n**Path:** <path>\n**Content:**\n<full content>`.

**b.2 — Launch Clarity perspective SYNCHRONOUSLY.** (depends on: b.1 shared prefix + per-perspective block 3a constructed)

Invoke `Agent(subagent_type="review-perspective-clarity", prompt=block1+block2+block3a+block4)` with a maximum wait of 5 minutes. If no response is received within 5 minutes, write a `{"status": "missing", "reason": "timeout"}` stub to `$CLAUDE_PLUGIN_DATA/audit/perspectives/<session_id>/clarity.json` and proceed to b.3. Awaiting first-token return on success also primes breakpoints 1 and 2 in the KV cache.

**b.3 — Launch Correctness + Integration perspectives in PARALLEL.** (depends on: b.2 returned or timed out)

In a single tool-use batch, issue two Agent calls with per-call 5-minute timeouts: `Agent(subagent_type="review-perspective-correctness", prompt=block1+block2+block3b+block4)` and `Agent(subagent_type="review-perspective-integration", prompt=block1+block2+block3c+block4)`. For any call that exceeds 5 minutes without response, write a `{"status": "missing", "reason": "timeout"}` stub for that perspective.

If any Agent tool call errors, times out, or the `subagent_type` is not one of the three perspective names, the `policy_gate.py` PreToolUse hook denies the call. Collect errors per perspective; do not abort the whole dispatch.

**b.4 — Write perspective certificates to audit-disk.** (depends on: b.2 and b.3 returning or timing out; produces: 3 files under `$CLAUDE_PLUGIN_DATA/audit/perspectives/<session_id>/`)

For each returned perspective certificate, use the Write tool to persist it at `$CLAUDE_PLUGIN_DATA/audit/perspectives/<session_id>/<perspective>.json`. File names are derived strictly from the orchestrator's constants `clarity|correctness|integration` — never from sub-agent output — to prevent path injection. Missing certificates write a `{"status": "missing"}` stub. b.5 must not begin until all three b.4 writes have completed (either with a real certificate or with a `missing`/`timeout`/`skipped` stub).

**b.5 — Merge findings via deterministic script.** (depends on: b.4 completed; produces: `merged.json`)

Invoke `Bash("python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge_findings.py $CLAUDE_PLUGIN_DATA/audit/perspectives/<session_id>")`. `policy_gate.py` allowlists only this exact invocation pattern and the escalation script below. Write the script's stdout JSON to `$CLAUDE_PLUGIN_DATA/audit/perspectives/<session_id>/merged.json`.

**b.6 — Decide escalation via deterministic script.** (depends on: b.5 merged.json exists and is valid JSON)

Invoke `Bash("python3 ${CLAUDE_PLUGIN_ROOT}/scripts/escalation_decision.py $CLAUDE_PLUGIN_DATA/audit/perspectives/<session_id>/merged.json")`. Append `--deep` when the user passed `--deep`. Capture `{escalation_required, reasons}`.

**b.7 — Handle degraded mode.** (depends on: b.5 merged.json parsed)

If `merged.status == "failure"` (all 3 perspectives null): abort with `## ERROR\nall perspectives failed: <missing_perspectives>`. If `merged.degraded_mode == true` (1-2 perspectives missing): proceed with emit but include `degraded_mode: true` + `missing_perspectives: [...]` in the certificate. Downstream consumers (`/apply-skill-review-findings`) must branch on this flag.

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
| Clarity | [A-F] | 15% | [One line — cite ≥1 checklist ID, e.g., "WS-2 FAIL: conditionals use 'if needed' without criteria"] |
| Completeness | [A-F] | 15% | [One line — cite ≥1 checklist ID, e.g., "WS-2 FAIL: conditionals use 'if needed' without criteria"] |
| Prompt Engineering | [A-F] | 15% | [One line — cite ≥1 checklist ID, e.g., "WS-2 FAIL: conditionals use 'if needed' without criteria"] |
| Context Engineering | [A-F] | 15% | [One line — cite ≥1 checklist ID, e.g., "WS-2 FAIL: conditionals use 'if needed' without criteria"] |
| Goal Alignment | [A-F] | 20% | [One line — cite ≥1 checklist ID, e.g., "WS-2 FAIL: conditionals use 'if needed' without criteria"] |
| Safety | [A-F] | [10/15%] | [One line — cite ≥1 checklist ID, e.g., "WS-2 FAIL: conditionals use 'if needed' without criteria"] |
| Metadata | [A-F] | [10/5%] | [One line — cite ≥1 checklist ID, e.g., "WS-2 FAIL: conditionals use 'if needed' without criteria"] |
| **Overall** | **[A-F]** | **100%** | **Weighted: XX.X** |

Calculate overall grade:
1. Determine weights: if skill has Write/Bash/Edit in allowed-tools, Safety=15% and Metadata=5%; otherwise Safety=10% and Metadata=10%. All other weights unchanged.
2. Convert grades: A=95, B=85, C=75, D=65, F=50.
3. Weighted score = sum(grade_value × weight) for all 7 dimensions.
4. Map back: ≥90→A, ≥80→B, ≥70→C, ≥60→D, <60→F.
5. Show in Overall Justification: "Weighted: XX.X → [Grade]"

### Grading Boundary Examples

See `references/boundary-exemplars.md` for the canonical B-vs-C boundary per dimension (Clarity, Safety non-agentic, Safety agentic, Completeness, Metadata).

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

### Merged Findings (multi-perspective mode only)

Merged findings are taken verbatim from `merged.json`. For each finding, emit using this template:

```
**<finding_id>** · Dimensions: [<dim1>, <dim2>] · Severity: <High|Medium|Low> · Perspectives: [<clarity|correctness|integration>]
- owner_conflict: <true|false> · hint_owner: <clarity|correctness|integration|null>
- path: <relative/path/to/file> · line_range: <N-M>
- **Evidence:** <exact quote from artifact>
- **Why:** <rubric/baseline justification>
- **Validation:** <how to confirm fix on re-review>
- **Current:** <existing text>
- **Recommended:** <concrete rewrite>
```

Example:

```
**RL-1:skills/foo/SKILL.md:Safety/v1** · Dimensions: [Safety] · Severity: High · Perspectives: [integration]
- owner_conflict: false · hint_owner: null
- path: skills/foo/SKILL.md · line_range: 42-48
- **Evidence:** "Await first-token return before proceeding — this primes breakpoints 1 and 2."
- **Why:** RL-1 requires an explicit termination predicate; no timeout defined.
- **Validation:** Body contains `<= N minutes` or step-cap per Agent call.
- **Current:** Invoke Agent(...). Await first-token return.
- **Recommended:** Invoke Agent(...) with max wait 5 min; on timeout write `{"status": "missing"}` stub.
```

### Owner-Conflict Signals (multi-perspective mode only)
[Findings with owner_conflict=true listed separately from graded findings. Each shows: checklist_item, hint_owner, evidence, and which perspective flagged it.]

### Escalation (multi-perspective mode only)
escalation_required: [true|false]
reasons: [list of ESC-1..5 triggers, or empty list]
design_deviations:
  - "Escalation is flag-only by default. Auto-re-run restricted to ESC-5 (degraded mode — missing/malformed certificates). On ESC-1/2/3/4, re-invoke as /review-skill --deep <path> to force Opus-tier escalation. See docs/roadmap-2026-04-19.md amendment."

degraded_mode: [true|false]
missing_perspectives: [list or empty]

## Phase 4 — Report Persistence (standalone mode only)

In orchestrated mode, skip this phase entirely — return only the structured certificate above.

In standalone mode:
1. Present the certificate to the user.
2. Confirm before writing: "Save review report to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-skill.md`?"
3. If confirmed, assemble the report using the canonical frontmatter contract located in Step 1 with:
   - `generated_by: review-skill`
   - one `summary` item of type `Skill`
   - `repo: <slug>` and optionally `origin: <git-remote-url>`
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

### Named failure classes

- **Bash script failure** (`merge_findings.py` or `escalation_decision.py` exits non-zero OR writes stdout that does not parse as JSON): emit `## ERROR <script>: <exit-code or stderr>` and stop. Exception: when `escalation_decision.py` specifically fails, do **not** abort — treat as `escalation_required: false, reasons: ["script-error"]` and set `escalation_script_error: true` in the certificate so the user can re-run with `/review-skill --deep <path>`.
- **Write failure in b.4** (perspective certificate persist): log the failure, continue, and return the perspective certificate content inline in the certificate output. Mark `write_failed: true, failed_perspectives: [...]` in the certificate.
- **Write failure in Phase 4** (report persist): log the failure, return the certificate inline to the user, and skip the commit-suggestion step. Mark `write_failed: true` in the output footer.
- **Agent call timeout** (b.2 or b.3 exceeds 5 min): treat the perspective as missing; write `{"status": "missing", "reason": "timeout"}` stub to its audit path; set `degraded_mode: true`; proceed to b.5. If ≥2 perspectives time out, `merge_findings.py` produces degraded-mode output — downstream consumers must branch accordingly.

## Hard Rules

- **Read-only on the analyzed skill.** Never modify the skill being reviewed. Write only to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/` and `$CLAUDE_PLUGIN_DATA/audit/perspectives/<session_id>/`.
- **Credential scope (PII/secret redaction).** Before writing content quoted from the analyzed skill to any audit or report path: (1) truncate `evidence` / `current` blocks at 500 characters, (2) redact token-like substrings matching `/[A-Za-z0-9_\-]{20,}/` with `<REDACTED>`, (3) skip writes entirely when the analyzed path matches `**/*.env`, `**/.ssh/**`, or `**/credentials.*` — emit a `{"status": "skipped", "reason": "credential-scope"}` stub instead.
- **Tier A tool justification:** Write + WebSearch/WebFetch + Agent + Bash are present because: (1) Write is restricted to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/` and `$CLAUDE_PLUGIN_DATA/audit/perspectives/<session_id>/` only, (2) WebSearch/WebFetch are for domain research, not file modification, (3) Agent is restricted via `hooks/policy_gate.py` PreToolUse allowlist to `subagent_type ∈ {review-perspective-clarity, review-perspective-correctness, review-perspective-integration}`; any other subagent_type is denied, (4) Bash is allowlisted by the same hook to exactly `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge_findings.py ...` and `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/escalation_decision.py ...`; any other command is denied, (5) read-only Hard Rule above prevents write-to-analyzed-file risk.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present the full certificate before any follow-up actions.**
