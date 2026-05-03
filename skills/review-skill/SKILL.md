---
name: review-skill
description: >
  Evaluates a single SKILL.md across 7 quality dimensions and produces an
  optimization certificate. Use when asked to 'review skill' or dispatched by
  /review-claude-config. Do NOT use for agents or rules — use /review-agent or
  /review-rule. Does NOT apply findings — use /apply-skill-review-findings to
  implement recommendations.
argument-hint: <path-to-SKILL.md>
allowed-tools: Read, Write, Glob, WebSearch, WebFetch, Agent, Bash
---

# Review Skill

Evaluate a single Claude Code skill for quality across 7 evidence-based dimensions.

## Argument Handling

- `$ARGUMENTS` is the path to a SKILL.md file.
- Optional flag `--compare-with <prior-merged.json>` — if present, after the new merge completes (b.5), invoke `scripts/check_convergence.py` against the prior `merged.json` and include the result in the Phase 3 certificate (b.8). Use to verify run-to-run convergence per the deterministic-subset contract in CLAUDE.md "Iterate reviews until convergence" rule.
- Optional flag `--deep` — forces Opus-tier escalation upfront (see Mode Detection).
- Optional flag `--single-perspective` — reverts to legacy single-perspective scoring.
- If `$ARGUMENTS` is empty, prompt the user: "Provide the path to a SKILL.md file to review." and stop.
- Validate the `$ARGUMENTS` path argument: confirm the file exists, the path conforms to the `*.md` pattern, and the file contains YAML frontmatter with a `name` field (required for skills).
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

Attempt a trivial WebSearch (e.g., "Claude Code documentation") with a 30-second timeout. If it fails or times out, set `websearch_available = false` and fall back to model-knowledge-only Goal-Alignment scoring. Goal Alignment will be scored from model knowledge only, marked `[no web verification]`.

Attempt a trivial WebFetch (e.g., fetch "https://docs.anthropic.com") with a 30-second timeout. If it fails or times out, set `webfetch_available = false` and fall back to skipping the optional URL fetch in Step A.

Attempt a trivial Bash probe: `Bash("echo ok")`. If it fails, set `bash_available = false`. In standalone mode when `bash_available = false`: skip b.5 and b.6 (merge + escalation scripts); emit the three unmerged perspective certificates directly in the Phase 3 output and include `degraded_mode: true, missing_perspectives: ["merge-script-unavailable"]`. This applies even when all three perspective calls succeed, because without merge there is no owner-weighted dimension grade.

### Step 1: Load References

The skill consumes 6 markdown references plus 1 conditional file. Each is
annotated with the consumer (where its content is used) and the load site
(where the Read call happens). This separation prevents multi-source
context-loading from blurring canonical vs. supporting scope (Kassner
mispriming — see `engineering-baseline.md` §"Distractor Isolation"). Five of
the six are loaded immediately below; the sixth (`boundary-exemplars.md`) is
loaded JIT in `b.1` only when multi-perspective dispatch fires.

Reference inventory (always present; load timing varies):

- `references/scoring-rubric.md` — grading criteria (consumed in Phase 2 Step B/B-multi rubric application; loaded now at Step 1)
- `references/engineering-baseline.md` — prompt, context, and tool-design techniques (consumed in Phase 2 Step A goal-inference and Phase 2 Step B/B-multi justification citations; loaded now at Step 1)
- `references/source-quality-criteria.md` — source filtering for web research (consumed in Phase 2 Step A domain research; loaded now at Step 1)
- `references/skill-evaluation-guide.md` — type-specific checklist PD-1 → IJ-1 (consumed in Phase 2 Step B/B-multi checklist walk; loaded now at Step 1 from this skill's own directory, NOT the sibling `review-claude-config` skill)
- `references/boundary-exemplars.md` — canonical B-vs-C boundaries per dimension (consumed in Phase 2 Step B-multi b.1 Block 2 cache prefix and Phase 3 §"Grading Boundary Examples"; loaded JIT at b.1 in multi-perspective mode only — declared here for inventory completeness, NO Read call at Step 1)
- `references/repo-identification.md` — `suite-root` / `repo-slug` resolution (consumed in Phase 4 standalone-mode report-path construction; loaded now at Step 1)

Locate the `review-claude-config` skill directory (sibling skill in the same
plugin) and read these references from it now, in the order listed:
`scoring-rubric.md`, `engineering-baseline.md`, `source-quality-criteria.md`,
`repo-identification.md`. The fifth always-now load is
`skill-evaluation-guide.md` from THIS skill's own `references/` directory
(not the sibling). Use Glob to find the files if the path is not immediately
known: `**/review-claude-config/references/scoring-rubric.md` (and analogous
for the others).

**If any of these files is not found, set `status: failure`, emit the error "Required reference not found. Ensure review-claude-config is installed as a sibling skill.", and stop.**

When the skill declares Write, Bash, Edit, or MCP tools in `allowed-tools`:
also read `**/review-claude-config/references/tool-grant-decision-tree.md`
for archetype alignment and high-risk combination evaluation (consumed in
Phase 2 Step B SP-2 / SP-4 evaluation only when tool-grant triggers fire).

## Phase 2 — Evaluation

Phase 2 contains two top-level sub-steps (Step A and Step B); when running multi-perspective dispatch (the default), Step B further decomposes into the granular steps b.0 through b.8.

### Step A: Goal Inference + Domain Research

1. Read the skill file and infer its primary goal/domain in one sentence.
2. Domain research (follow orchestration flags if in orchestrated mode):
   - First, check the domain cache: Read `${CLAUDE_PLUGIN_ROOT}/skills/review-claude-config/references/domain-cache/INDEX.md` and match the skill's domain to a universal cache entry.
   - If `CACHED` (entry exists, ≤90 days old): read the cache file and use as primary domain knowledge. At most 1 supplemental WebSearch query if the cache lacks coverage for this skill's specific area.
   - If `STALE` (≥90 days): perform 1 WebSearch query to refresh.
   - If no cache entry matches: extract domain keywords from the skill's description and content, then perform 1-2 targeted WebSearch queries (technology + workflow + quality aspect, not generic "best practices"). If `webfetch_available == true` AND a single most-relevant URL is identified by the WebSearch results, fetch that URL with a 30-second timeout; on timeout or fetch error, fall back to model-knowledge-only Goal-Alignment scoring without the URL content. Otherwise (no URL identified, or `webfetch_available == false`) skip WebFetch.
   - If neither cache nor WebSearch available: use model knowledge only, marked `[no external verification]`.
   - Apply source quality criteria (loaded above or from shared reference materials in orchestrated mode): discard marketing/opinion/outdated content, prefer Tier 1-2 sources, cross-validate claims used in Goal Alignment scoring.
3. Synthesize: what should a high-quality skill in this domain include?

**Resource caps (hard limits per review):** ≤3 WebSearch queries, ≤1 WebFetch call, ≤10 reference file reads. Exceeding these indicates scope creep — narrow the research focus rather than broadening.

### Step B — Scoring + Recommendations (legacy / orchestrated mode + `--single-perspective`)

Applied when `mode: orchestrated` OR user passed `--single-perspective` flag.

Score using the rubric as the PRIMARY basis. The skill evaluation guide provides type-specific criteria. Domain research informs Goal Alignment and enriches recommendations but does NOT alter scoring criteria for other dimensions.

**Scoring procedure:**

1. Work through the full checklist in `references/skill-evaluation-guide.md` exactly once: for each of the items PD-1 through IJ-1 (the finite, enumerated list ending at IJ-1), record a PASS, FAIL, or NA verdict. RD-1 through RD-6 are reliability diagnostic checks — their FAILs are surfaced in the `### Reliability Diagnostics` output section and contribute to the mapped dimension grade (RD-1/2/3 → Metadata; RD-4 → Completeness; RD-5 → Clarity; RD-6 → Safety). For RD-3, Glob for sibling `SKILL.md` files in the same plugin directory and compare trigger phrases.
2. **Completeness gate — success condition.** Review is complete when ALL of the following hold (binary, not judgement-based):
   - Every checklist item (PD-1 through IJ-1) has a PASS/FAIL/NA verdict. Count verdicts; if `verdict_count != expected_count`, list the missing item IDs explicitly and evaluate each before proceeding. Do not advance until `verdict_count == expected_count`.
   - Every dimension has at least one non-NA item with a cited checklist ID.
   - The certificate table in Phase 3 has exactly 7 dimension rows plus Overall.
   - Every High or Medium finding carries non-empty `Evidence`, `Why it matters`, and `Validation` blocks.
   - Every High/Medium finding cites ≥1 verbatim evidence quote from the artifact under review (evidence-citation predicate).
   - When `--compare-with <prior>` is supplied, the deterministic finding_id set must be identical across runs and `<= 1 letter Δ` max_grade_variance per dimension (convergence predicate).
3. Score each dimension using the rubric, referencing checklist results as evidence. Justification lines in the certificate must cite at least one checklist ID (e.g., "WS-2 FAIL: conditionals use 'if needed' without criteria").
4. **Self-check before emit.** Recompute the weighted score (grade-value × weight per dimension, summed). Verify the weights sum to exactly 100%. Verify the row count equals 7 dimensions + Overall. Verify every High/Medium finding has non-empty Evidence and Validation. If any check fails, correct the certificate before emitting.
5. The completed checklist is an internal working artifact — do not include it verbatim in the output certificate.

### Step B-multi — Multi-Perspective Dispatch (standalone mode default)

Applied when standalone AND user did NOT pass `--single-perspective`.

Load `references/perspective-dispatch-protocol.md` and `skills/review-claude-config/references/merge-rules.md` JIT. Those files contain the authoritative recipe; the sub-steps below are the orchestration sequence.

**Context budget / masking strategy.** The multi-perspective dispatch produces ≥ 16 tool-call turns (1 pre-dispatch Bash + 3 Agent calls + up to 10 reference Reads + 2 Bash invocations + 3 Writes). Masking is achieved by **non-re-retrieval via disk-based handoff**: intermediate perspective certificates (≤ 4 K tokens each) are written to disk in b.4 and thereafter referenced only by path. The merge in b.5 consumes `merged.json` produced by a deterministic script, not the raw perspective output in the conversation history. No LLM summarisation step is used, so no summarisation justification is required per CE-X.

**b.0 — Deterministic binary evaluation.** (produces: `binary_verdicts.json`)

Invoke `Bash("python3 ${CLAUDE_PLUGIN_ROOT}/scripts/rubric_binary_evaluator.py <artifact-path>")`. Capture the stdout JSON and write the captured JSON to `${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/binary_verdicts.json` using the Write tool.

Exit-code handling (exception to the "Bash script failure" rule under §Error Handling — see Named Failure Classes):

- exit 0 — stats.runner_error == 0; write the full verdicts JSON, proceed to b.1.
- exit 2 — stats.runner_error > 0 but partial verdicts are present; write the JSON, proceed to b.1. The evaluator status will be labeled `"error"` in the merged cert but verdicts still apply.
- exit 1 — global crash; do NOT abort the review. Write a `{"status": "crashed", "verdicts": {}}` stub to `binary_verdicts.json` and proceed to b.1. The merge layer will skip Layer 1.5 caps (see `skills/review-claude-config/references/merge-rules.md` §"Missing or malformed `binary_verdicts.json`") and perspective findings on binary items are NOT dropped.

Verdicts are consumed only by b.5 merge — they are NOT injected into the perspective prompts constructed in b.1.

**b.1 — Build shared prefix + per-type block + per-perspective suffixes.**

- Block 1 (shared prefix, byte-identical across all 3 perspectives): concatenate `scoring-rubric.md` + `engineering-baseline.md` + `source-quality-criteria.md` + the shared perspective wrapper sentence. ~6,100 Opus-4.7 tokens. Mark `cache_control` on this block.
- Block 2 (per-type block, byte-identical across 3 perspectives for skill review): `skill-evaluation-guide.md` + `boundary-exemplars.md`. ~1,850 tokens. Mark `cache_control`.
- Block 3 (per-perspective, differs per sibling): functional role + ownership contract + output-schema reminder from the matching agent's SKILL frontmatter + body top. ~400 tokens each. Mark `cache_control`.
- Block 4 (artifact, uncached): `## Item Under Review\n**Path:** <path>\n**Content:**\n<full content>`.

**b.2 — Launch Clarity perspective SYNCHRONOUSLY.** (depends on: b.1 shared prefix + per-perspective block 3a constructed)

Invoke `Agent(subagent_type="review-perspective-clarity", prompt=block1+block2+block3a+block4)` with a maximum wait of 5 minutes. If no response is received within 5 minutes, write a `{"status": "missing", "reason": "timeout"}` stub to `${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/clarity.json` and continue to b.3 (fall back to merging the remaining perspective certificates). Awaiting first-token return on success also primes breakpoints 1 and 2 in the KV cache.

**b.3 — Launch Correctness + Integration perspectives in PARALLEL.** (depends on: b.2 returned or timed out)

In a single tool-use batch, issue two Agent calls with per-call 5-minute timeouts: `Agent(subagent_type="review-perspective-correctness", prompt=block1+block2+block3b+block4)` and `Agent(subagent_type="review-perspective-integration", prompt=block1+block2+block3c+block4)`. For any call that exceeds 5 minutes without response, write a `{"status": "missing", "reason": "timeout"}` stub for that perspective and fall back to merging the remaining certificates.

If any Agent tool call errors, times out, or the `subagent_type` is not one of the three perspective names, the `policy_gate.py` PreToolUse hook denies the call. Collect errors per perspective and write a `{"status": "missing", "reason": "denied"}` stub to that perspective's audit path; do not abort the whole dispatch — fall back to continuing with the surviving perspectives.

**b.4 — Write perspective certificates to audit-disk.** (depends on: b.2 and b.3 returning or timing out; produces: 3 files under `${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/`)

For each of the 3 returned perspective certificates (clarity, correctness, integration) — max 3 iterations, stop when all three audit-paths are written or stubbed — use the Write tool to persist the certificate at `${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/<perspective>.json`. The cert is produced by `scripts/perspective_certificate_parser.py::parse_perspective_certificate`, which converts the agent's Markdown grade-table into the canonical shape (see `skills/review-claude-config/references/merge-rules.md` §"Inputs" for the JSON example; the parser is the authoritative producer, the example illustrates the output). The grade map MUST be persisted under the top-level key `dimensions` (the parser's output key) — `merge_findings.py:357` reads `cert.get("dimensions", {})`, so any other alias (e.g., `grades`) defaults every dimension to F at the merge layer. File names are derived strictly from the orchestrator's constants `clarity|correctness|integration` — never from sub-agent output — to prevent path injection. Missing certificates write a `{"status": "missing"}` stub. b.5 must not begin until all three b.4 writes have completed; once every slot holds either a real certificate or a `{"status": "missing"}` stub (covering timed-out, denied, or skipped perspectives), continue to b.5.

For malformed agent output (parser raises an exception, `dimensions` key absent, or grade table cannot be extracted), write a `{"status": "parse_error", "reason": "<parser stderr or exception summary>"}` stub to the same audit path instead of the partial certificate; the orchestrator MUST construct this JSON via `json.dumps()` (Python) or an equivalent JSON-escaping primitive — never via raw string formatting — to prevent attacker-controlled bytes in the parser stderr from breaking JSON well-formedness or escaping the `reason` field. Treat the perspective as missing for downstream merge purposes (b.5 sees the stub like any other missing perspective and applies the same degraded-mode logic), and surface `agent_output_validation: {total: 3, parsed: <count>, failed: <count>}` in the merged-cert footer so operators can distinguish a transient parser failure from a perspective that genuinely declined to grade.

**b.5 — Merge findings via deterministic script.** (depends on: b.0 and b.4 completed; produces: `merged.json` + `findings.json`)

Invoke `Bash("python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge_findings.py ${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id> --findings-out ${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/findings.json")`. The merge script reads the three perspective certificates PLUS `binary_verdicts.json` (produced in b.0), synthesizes deterministic findings for each binary FAIL, applies Layer 1.5 grade caps, and drops perspective findings on binary items + narrative parents (see `skills/review-claude-config/references/merge-rules.md`). Write the script's stdout JSON to `${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/merged.json`. The `--findings-out` flag emits a schema-validated `findings.json` sidecar (per `skills/review-claude-config/references/schemas/findings-list.schema.json`) into the same directory; this sidecar is the authoritative machine-parsable input for `/apply-skill-review-findings` and replaces the legacy Markdown-heading regex parse.

**b.6 — Decide escalation via deterministic script.** (depends on: b.5 merged.json exists and is valid JSON)

Invoke `Bash("python3 ${CLAUDE_PLUGIN_ROOT}/scripts/escalation_decision.py ${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/merged.json")`. Append `--deep` when the user passed `--deep`. Capture `{escalation_required, reasons}`.

**b.7 — Handle degraded mode.** (depends on: b.5 merged.json parsed)

If `merged.status == "failure"` (all 3 perspectives null): set `status: failure`, emit `## ERROR\nall perspectives failed: <missing_perspectives>`, and stop (terminal state — no certificate produced). If `merged.degraded_mode == true` (1-2 perspectives missing): fall back to emitting the certificate with `degraded_mode: true` + `missing_perspectives: [...]` included. Downstream consumers (`/apply-skill-review-findings`) must branch on this flag.

**b.8 — Convergence check vs. prior run.** (optional, depends on b.7; fires only when `--compare-with <prior>` was passed)

If the user supplied `--compare-with <prior-merged.json>`, invoke `Bash("python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_convergence.py <prior-merged.json> ${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/merged.json")`. Capture the script's stdout JSON. Exit-code handling:

- `0` (converged) — record `convergence: {converged: true, ...}` in the cert.
- `1` (not converged) — record `convergence: {converged: false, ...}`. Append `ESC-5` to escalation reasons (re-run signal) unless ESC-5 was already raised by b.6.
- `2` (script error) — record `convergence: {converged: null, error: "<stderr>"}`. Do NOT abort the review; fall back to surfacing the script-error in the cert and continue to Phase 3.

When `--compare-with` is absent, b.8 is skipped silently — no convergence section appears in Phase 3.

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

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`. Prefer the `skills/` copy when present; otherwise use the sibling `.claude/skills/` copy. Apply the shared recommendation schema from the located contract below. Keep the skill-specific category vocabulary below.

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
- **Why:** RL-1 requires an explicit termination predicate; no upper-bound wait is specified.
- **Validation:** Body contains `<= N minutes` or step-cap per Agent call.
- **Current:** Invoke Agent(...). Await first-token return.
- **Recommended:** Invoke Agent(...) with max wait 5 min; on expiry, fall back to writing a `{"status": "missing"}` stub.
```

### Owner-Conflict Signals (multi-perspective mode only)
[Findings with owner_conflict=true listed separately from graded findings. Each shows: checklist_item, hint_owner, evidence, and which perspective flagged it.]

### Convergence (multi-perspective mode only — present only when `--compare-with` was supplied)

```yaml
convergence:
  converged: [true|false|null]   # null = script error
  deterministic_added_finding_ids: [list]    # H/M findings present in new but not prior
  deterministic_removed_finding_ids: [list]  # H/M findings present in prior but not new
  max_grade_variance: <int>                  # max letter distance per dimension
  null_dimensions_added: [list]              # dimensions lost between runs
  prior: <path>                              # echo of --compare-with argument
  error: "<message>"                         # only when converged: null
```

When `converged: false`, the per-finding diff lists give the reviewer a precise picture of what flapped. The merged.json itself is not modified — the convergence section is summary metadata.

### Escalation (multi-perspective mode only)
escalation_required: [true|false]
reasons: [list of ESC-1..5 triggers, or empty list]
design_deviations:
  - "Escalation is flag-only by default. Auto-re-run restricted to ESC-5 (degraded mode — missing/malformed certificates). On ESC-1/2/3/4, re-invoke as /review-skill --deep <path> to force Opus-tier escalation. See Plans/claude-code-hat-in-validated-seahorse.md:201 amendment."

degraded_mode: [true|false]
missing_perspectives: [list or empty]

## Phase 4 — Report Persistence (standalone mode only)

In orchestrated mode, skip this phase entirely — return only the structured certificate above.

In standalone mode:
1. Present the certificate to the user.
2. Confirm before writing: "Save review report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-skill.md`?"
3. If confirmed, assemble the report using the canonical frontmatter contract located in Step 1 with:
   - `generated_by: review-skill`
   - one `summary` item of type `Skill`
   - `repo: <slug>` and optionally `origin: <git-remote-url>`
   - `type + path` as the canonical identity and `name` as display-only
4. Write the report file. Suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report`
5. **Persist findings.json sidecar (multi-perspective mode only).** When b.5 produced `${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/findings.json`, copy it atomically to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-skill.findings.json` (sibling of the `.md` report — same prefix, `.findings.json` suffix) via `Bash("cp <audit-side> <report-side>.tmp && mv <report-side>.tmp <report-side>")`. The tmp+rename pattern prevents a partial-write window where `/apply-skill-review-findings` could read a half-flushed sidecar. The sidecar conforms to `skills/review-claude-config/references/schemas/findings-list.schema.json` and is the authoritative input for `/apply-skill-review-findings`. In `--single-perspective` or orchestrated mode no sidecar is emitted; apply-* falls back to Markdown parsing for back-compat with legacy reports.
6. **What's Next?** (standalone mode only — skip in orchestrated mode)

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

- **`merge_findings.py` failure** (non-zero exit OR stdout not valid JSON): construct a stub via `json.dumps()` (Python) or an equivalent JSON-escaping primitive — `{"status": "script_error", "stderr": "<captured stderr>", "degraded_mode": true, "missing_perspectives": ["merge-failed"]}` — and write the stub directly to `${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/merged.json`. The `degraded_mode` and `missing_perspectives` keys MUST be inside this JSON object so `escalation_decision.py`'s ESC-5 trigger reads them. Use a JSON-escaping primitive (never raw string concatenation) so attacker-controlled bytes in the merge-script stderr cannot break JSON well-formedness or escape the `stderr` field. Then continue to b.6 unchanged. b.6 invokes `escalation_decision.py` against the stub merged.json; the script reads `degraded_mode: true` and emits `escalation_required: true, reasons: ["ESC-5: degraded mode — missing perspectives: merge-failed"]`. The user re-runs with `/review-skill --deep <path>` to recover. This is symmetric with `escalation_decision.py` failure handling and keeps a single hard-abort path: only Phase 1 reference-not-found remains terminal.
- **`escalation_decision.py` failure** (non-zero exit OR stdout not valid JSON): fall back to `escalation_required: false, reasons: ["script-error"]` and set `escalation_script_error: true` in the certificate so the user can re-run with `/review-skill --deep <path>`.
- **`rubric_binary_evaluator.py` exit-code-specific rules** (overrides the generic "Bash script failure" rule above for this script):
  - exit 0 — success; write verdicts file, proceed.
  - exit 2 — partial verdicts present; write verdicts file, proceed. Merged cert records `binary_evaluator_status: "error"`.
  - exit 1 — global crash; write a `{"status": "crashed", "verdicts": {}}` stub to `binary_verdicts.json`, proceed. Merge layer skips Layer 1.5 caps and retains perspective findings on binary items.
  - In all three branches the review continues; the evaluator never aborts the dispatch.
- **Write failure in b.4** (perspective certificate persist): log the failure, continue, and return the perspective certificate content inline in the certificate output. Mark `write_failed: true, failed_perspectives: [...]` in the certificate.
- **Write failure in Phase 4** (report persist): log the failure, return the certificate inline to the user, and skip the commit-suggestion step. Mark `write_failed: true` in the output footer.
- **Agent call timeout** (b.2 or b.3 exceeds 5 min): fall back to treating the perspective as missing — write a `{"status": "missing", "reason": "expired"}` stub to its audit path, set `degraded_mode: true`, and continue to b.5. If ≥2 perspectives time out, `merge_findings.py` produces degraded-mode output — downstream consumers must branch accordingly.

## Hard Rules

- **Read-only on the analyzed skill.** Never modify the skill being reviewed. Write only to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` and `${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/`.
- **Credential scope (PII/secret redaction).** Before writing content quoted from the analyzed skill to any audit or report path: (1) truncate `evidence` / `current` blocks at 500 characters, (2) redact token-like substrings matching `/[A-Za-z0-9_\-]{20,}/` with `<REDACTED>`, (3) skip writes entirely when the analyzed path matches `**/*.env`, `**/.ssh/**`, or `**/credentials.*` — emit a `{"status": "skipped", "reason": "credential-scope"}` stub instead.
- **Tier A tool justification:** Write + WebSearch/WebFetch + Agent + Bash are present because: (1) Write is restricted to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` and `${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/` only, (2) WebSearch/WebFetch are for domain research, not file modification, (3) Agent is used exclusively for the three review-perspective-* sub-agents (any other `subagent_type` is a protocol violation), (4) Bash is used for: three `python3` invocations — `scripts/rubric_binary_evaluator.py` (b.0 pre-dispatch), `scripts/merge_findings.py` (b.5), `scripts/escalation_decision.py` (b.6) — plus an optional `scripts/check_convergence.py` (b.8 when `--compare-with` is supplied), and two atomic-copy commands (`cp` + `mv`) at Phase 4 step 5 to persist the findings.json sidecar from `${HOME}/.claude/plugins/data/claude-config/audit/perspectives/<session_id>/` to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`. Command-level permission is enforced by `.claude/settings.local.json` (`"Bash(python3 *)"` plus `"Bash(cp:*)"` and `"Bash(mv:*)"` for the atomic copy). `hooks/policy_gate.py` is an opt-in level-based (L1-L5) audit hook and applies no command-level allowlist when no `${HOME}/.claude/plugins/data/claude-config/policy.json` is present, (5) read-only Hard Rule above prevents write-to-analyzed-file risk.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present the full certificate before any follow-up actions.**
