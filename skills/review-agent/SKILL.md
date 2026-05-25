---
name: review-agent
description: >
  Evaluates a single agent .md across 7 dimensions including activation
  precision and trigger coverage. Use when asked to 'review agent' or
  dispatched by /review-claude-config. Do NOT use for skills or rules — use
  /review-skill or /review-rule.
argument-hint: <path-to-agent.md>
allowed-tools: Bash, Read, Write, Glob, WebSearch, WebFetch
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

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)

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

## Quality measurement (mandatory before Phase 4)

Without verification, this skill fails at CONVERGENCE-DRIFT (the same agent .md produces non-identical High+Medium `finding_id` sets across consecutive runs because the rubric's `DA-2`/`DA-2b` activation-precision items are LLM-judged and the merge step inconsistently retains advisory perspective findings), CITATION-ROT (the Goal-Alignment dimension cites URLs/arXiv IDs that were not actually resolved in the producing session — reconstructed from training data instead of WebSearch tool-use), and ADVISORY-LEAKAGE (an advisory item like `WS-1` / `OF-3` / `PD-1` escapes the merge-time Low demotion per `references/merge-rules.md` §"Perspective Finding Handling" and ships at High or Medium). The three-layer pipeline below catches all three plus agent-specific TYPE-MISMATCH (Hook/Rule dimensions appearing in an Agent report) and activation-collision recall gaps (RD-3 territory where the agent's trigger phrases overlap with sibling agents' triggers).

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (Jiang et al. ACL 2024), Beyond Consensus (NUS 2025), `references/review-report-contract.md`, `references/merge-rules.md`, `references/scoring-rubric.md`, `references/agent-evaluation-guide.md`.

Run the pipeline against the assembled Phase 3 certificate. Compute `REPORT_PATH` as the path the Phase 4 step 4 Write will use; if no path is available yet (orchestrated mode), serialize the certificate to a tempfile for the duration of this section.

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the assembled report. STRICT failures block Phase 4; SOFT warnings surface in Output.

```bash
python3 - "$REPORT_PATH" "${PRIOR_MERGED_JSON:-}" <<'PY'
import sys, re, json, os
from pathlib import Path

REPORT = Path(sys.argv[1])
PRIOR  = sys.argv[2]

SEVERITY_VOCAB = {"High","Medium","Low"}
DIM_SET = {"clarity","completeness","prompt_engineering","context_engineering",
           "goal_alignment","safety","metadata"}
GRADE_VOCAB = {"A","B","C","D","F"}
URL_RE   = r"https?://[^\s)`\"<>]+"
CITE_RE  = r"\b(arXiv:[0-9.]+|RFC\s*[0-9]+|DOI:[^\s)]+)"
FIND_RE  = r"^####\s+\d+\.\s+.+\(Impact:\s*(High|Medium|Low)"
FM_RE    = r"\A---\n(.*?)\n---\n"
ID_RE    = r"ID:\s*([A-Z][A-Z0-9-]+:[^,\s)]+/v1)"
HOME_RE  = re.compile(r"^target\s*:\s*/(?:Users|home)/[^/\s]+/", re.M)

errors, warns = [], []
text = REPORT.read_text()
m = re.match(FM_RE, text, re.S)
if not m:
    errors.append("STRICT: report missing YAML frontmatter"); print("\n".join(errors)); sys.exit(1)
fm = m.group(1)

for k in ["generated_by","schema_version","date","repo","target","items_reviewed"]:
    if not re.search(rf"^{k}\s*:", fm, re.M):
        errors.append(f"STRICT: frontmatter missing required field '{k}'")
gb = re.search(r"^generated_by\s*:\s*(\S+)", fm, re.M)
if gb and gb.group(1) != "review-agent":
    errors.append(f"STRICT: generated_by must be 'review-agent', got '{gb.group(1)}'")
if HOME_RE.search(fm):
    errors.append("STRICT: frontmatter 'target' uses expanded home prefix; must use literal $HOME/")

# Type discipline — single summary row of type Agent (TYPE-MISMATCH)
typ_rows = re.findall(r"^\s*type\s*:\s*(\S+)", fm, re.M)
if not typ_rows:
    errors.append("STRICT: summary[] missing type field")
elif any(t.rstrip(",") != "Agent" for t in typ_rows):
    errors.append(f"STRICT: review-agent must emit type=Agent rows only, got {typ_rows}")

sections = [s.group(1).strip() for s in re.finditer(r"^##\s+(.+)$", text, re.M)]
order = ["Goal","Certificate","Strengths","Recommendations"]
pos = {k: next((i for i,s in enumerate(sections) if s.startswith(k)), -1) for k in order}
if any(v == -1 for v in pos.values()):
    errors.append(f"STRICT: missing required section heading from {order}; found={sections}")
elif sorted(pos.values()) != list(pos.values()):
    errors.append("STRICT: section order violates Goal->Certificate->Strengths->Recommendations")

# Dimension presence — full 7 dims for Agent type
for dim in DIM_SET:
    mm = re.search(rf"\b{dim}\s*:\s*(\S+)", fm)
    if not mm:
        errors.append(f"STRICT: summary missing dimension '{dim}'")
        continue
    v = mm.group(1).rstrip(",")
    if v not in GRADE_VOCAB and v != "null":
        errors.append(f"STRICT: dimension {dim}='{v}' not in {{A,B,C,D,F,null}}")

findings = re.findall(FIND_RE, text, re.M)
for sev in findings:
    if sev not in SEVERITY_VOCAB:
        errors.append(f"STRICT: finding severity '{sev}' not in {SEVERITY_VOCAB}")
blocks = re.split(r"^####\s+\d+\.", text, flags=re.M)[1:]
for i, b in enumerate(blocks, 1):
    for sub in ["Evidence","Why it matters","Validation"]:
        if not re.search(rf"\b{sub}\b", b):
            errors.append(f"STRICT: finding #{i} missing required sub-block '{sub}'")

# Activation-precision evidence anchor — at least one DA-* / TC-* checklist
# citation in Evidence blocks when High/Medium findings exist on Clarity or
# Metadata dims (rubric §"Item Inventory" requires checklist-ID justification).
hm_findings = [b for b in blocks if re.search(r"Impact:\s*(High|Medium)", b)]
if hm_findings:
    anchored = sum(1 for b in hm_findings if re.search(r"\b(DA-\d|TC-\d|AH-\d|RL-\d|AF-\d)\b", b))
    if anchored == 0:
        warns.append("SOFT: no High/Medium finding cites an agent-evaluation-guide checklist ID (DA-*/TC-*/AH-*/RL-*/AF-*)")

advisory_ids = {"WS-1","OF-3","OF-4","PE-4","CE-3","PD-1","RF-1"}
leaked = []
for h in re.finditer(r"####\s+\d+\.\s+.+\(Impact:\s*(High|Medium|Low)[^)]*ID:\s*([A-Z0-9-]+):", text):
    sev, item = h.group(1), h.group(2)
    if item in advisory_ids and sev in {"High","Medium"}:
        leaked.append(f"{item}@{sev}")
if leaked:
    errors.append(f"STRICT: advisory items leaked at High/Medium severity: {leaked}")

urls  = set(re.findall(URL_RE,  text))
cites = set(c if isinstance(c,str) else c[0] for c in re.findall(CITE_RE, text))
warns.append(f"INFO: urls={len(urls)} cites={len(cites)} (Layer B verifies resolution)")

if PRIOR and os.path.exists(PRIOR):
    prior = json.loads(Path(PRIOR).read_text())
    cur = set(re.findall(ID_RE, text))
    prev = {f["finding_id"] for f in prior.get("findings",[])
            if f.get("severity") in {"High","Medium"}
            and f.get("checklist_item") not in advisory_ids}
    drift = cur ^ prev
    if drift:
        errors.append(f"STRICT: convergence drift on H+M deterministic-subset: lost={sorted(prev-cur)} gained={sorted(cur-prev)}")

print(f"=== Layer A — {REPORT.name} ===")
for w in warns:  print(f"warn  {w}")
for e in errors: print(f"FAIL  {e}")
print(f"--- {len(errors)} STRICT, {len(warns)} SOFT ---")
sys.exit(1 if errors else 0)
PY
```

What each metric catches: frontmatter required-fields + `$HOME/` literal → DIMENSION-GRADE-ABSENCE and the `block-sensitive-content.sh` PreToolUse contract; `type=Agent` row check → TYPE-MISMATCH (a misrouted `/review-rule` or `/review-skill` body would emit a different type); section order → structural validity; dimension-presence (7 dims for Agent type) → DIMENSION-GRADE-ABSENCE; severity vocabulary + finding sub-blocks → SEVERITY-MISCALIBRATION (form-level only); activation-precision SOFT anchor → recall gap on agent-specific checklist citation (DA-*/TC-*/AH-*/RL-*/AF-*); advisory-leakage scan → ADVISORY-LEAKAGE; convergence diff against prior `merged.json` → CONVERGENCE-DRIFT.

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent whose ONLY task is to find what the report MISSED, FABRICATED, or MIS-CLASSIFIED versus the agent .md under review. Adversarial framing is load-bearing — non-adversarial dispatch loses CITATION-ROT and activation-collision recall.

```
Agent({
  description: "Adversarial review-agent report critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer. Two markdown files are attached: ARTIFACT " +
    "and REPORT. Neither label tells you which is which until you read " +
    "them. ARTIFACT is a Claude Code subagent .md under review (YAML " +
    "frontmatter with description/tools/model + prose body). REPORT is " +
    "the review certificate emitted by /review-agent.\n\n" +
    "Your only task is to find what the REPORT got wrong. List every " +
    "item that meets one of:\n" +
    "- MISSING — a defect actually present in ARTIFACT that REPORT does " +
    "  not flag (cite the line, name the rubric dimension it violates). " +
    "  Pay special attention to activation-collision findings (the " +
    "  agent's description triggers overlap with another agent's " +
    "  triggers — RD-3 territory) and missing-arg handling gaps (AH-2b).\n" +
    "- FABRICATED — a finding in REPORT whose claimed Evidence quote " +
    "  does not appear verbatim in ARTIFACT (cite finding heading + " +
    "  absent quote).\n" +
    "- MIS-SEVERITY — a finding whose severity (High|Medium|Low) is " +
    "  inconsistent with its evidence per the rubric grade caps.\n" +
    "- MIS-CITED — a URL, arXiv ID, RFC, or references/*.md citation in " +
    "  REPORT that reads as reconstructed-from-memory rather than " +
    "  resolved-in-session (broken link, wrong file, no tool-response).\n" +
    "- UNCITED — a quantitative or evidence-based claim in REPORT with " +
    "  no citation at all.\n" +
    "- FALSE-RESOLUTION — a finding the REPORT claims resolved (delta " +
    "  section) whose underlying defect still appears in ARTIFACT.\n" +
    "- ADVISORY-AT-HIGH — a finding whose checklist_item is in the " +
    "  advisory set {WS-1, OF-3, OF-4, PE-4, CE-3, PD-1, RF-1} shipped " +
    "  at severity High or Medium (must be Low per merge-rules).\n" +
    "- TYPE-MISMATCH — REPORT emits a dimension grade for a dimension " +
    "  not in the Agent dimension set (must be the full 7), or omits " +
    "  one of {clarity, completeness, prompt_engineering, " +
    "  context_engineering, goal_alignment, safety, metadata}.\n\n" +
    "Do not rate quality. Do not praise. Do not propose fixes. List " +
    "items only. Quote the literal sentence and name which file. Report " +
    "under 500 words.\n\n" +
    "ARTIFACT:\n<paste agent .md contents>\n\n" +
    "REPORT:\n<paste certificate contents>"
})
```

**Dispatch twice with order swapped** (ARTIFACT↔REPORT label position) — position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791). Take the union of items flagged across both runs.

### Layer C — binary rubric reconciliation

Six binary dimensions, each yes/no, each tied to ≥1 failure class. Any `NO` blocks Phase 4 until resolved.

```
D1 CONVERGENCE_STABILITY  When --compare-with prior merged.json supplied, the set of
                          finding_id values at severity in {High, Medium} on the
                          deterministic subset (per merge-rules.md §"Perspective
                          Finding Handling") is byte-identical between runs.
                          (Catches: CONVERGENCE-DRIFT)

D2 SEVERITY_JUSTIFIED     Every finding's severity matches its evidence per the
                          rubric §"Grade Caps" + §"Item Inventory"; no Layer-B
                          MIS-SEVERITY or ADVISORY-AT-HIGH item open.
                          (Catches: SEVERITY-MISCALIBRATION, ADVISORY-LEAKAGE)

D3 DIMENSION_COVERAGE     All 7 dimensions for Agent type appear in summary[]
                          with grade in {A,B,C,D,F,null}; no row is missing a
                          required dimension; type field equals "Agent" on every
                          summary row (no Hook/Rule/Skill row in a review-agent
                          report); no Layer-B TYPE-MISMATCH item open.
                          (Catches: DIMENSION-GRADE-ABSENCE, TYPE-MISMATCH)

D4 EVIDENCE_RESOLVED      Every URL, arXiv ID, RFC, and references/*.md path
                          cited in REPORT was either resolved in the producing
                          session (verifiable from tool-use log) OR carries an
                          explicit `[no web verification]` / `[unverified-url]`
                          marker; no MIS-CITED or UNCITED Layer-B item open.
                          (Catches: CITATION-ROT, UNCITED)

D5 NO_FABRICATED_FINDINGS Every finding's Evidence block contains a literal
                          quote from the analyzed agent .md; every High/Medium
                          finding cites at least one agent-evaluation-guide
                          checklist ID (DA-*/TC-*/AH-*/RL-*/AF-*); no
                          FABRICATED or FALSE-RESOLUTION Layer-B item open.
                          (Catches: SEVERITY-MISCALIBRATION false-positive
                          class, FALSE-FIX-PASS, activation-precision recall)

D6 SCOPE_DISCIPLINE       No advisory checklist_item ships at non-Low severity;
                          frontmatter `target:` uses the literal `$HOME/` token
                          (not the expanded home prefix); the single summary[]
                          row is keyed on `(repo, generated_by=review-agent,
                          type=Agent, path)` — never on name alone.
                          (Catches: ADVISORY-LEAKAGE, sensitive-content
                          contract violation)
```

Map Layer-A failures → D3/D4. Map Layer-B `MISSING` / `FABRICATED` → D5. Map `MIS-SEVERITY` / `ADVISORY-AT-HIGH` → D2. Map `MIS-CITED` / `UNCITED` → D4. Map `FALSE-RESOLUTION` → D5. Map `TYPE-MISMATCH` → D3.

### Reconciliation outcomes

- **All Layer-A STRICT pass + zero Layer-B `MISSING`/`FABRICATED`/`FALSE-RESOLUTION`/`ADVISORY-AT-HIGH`/`TYPE-MISMATCH`** → proceed to Phase 4.
- **Any Layer-A STRICT fail OR any of those Layer-B classes** → propose restorations inline (name each finding to add/remove with the artifact line + rubric citation), re-run Layer A on the patched report. Max two iterations. If still failing at iteration 2, surface to user and do NOT auto-write the report.
- **Only Layer-A SOFT warnings + Layer-B `MIS-SEVERITY` / `MIS-CITED` / `UNCITED` items** → record in Phase 4 Output under `### Layer-B Findings (Advisory)` and proceed. These do not block ship; reviewer triages.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Cross-report convergence beyond H+M deterministic subset** — D1 is bounded to High+Medium finding_ids on the deterministic subset per `merge-rules.md` §"Convergence Policy". Low-severity advisory drift is by-design unbounded. If a reviewer silently moves a deterministic finding into the advisory class (emitting it with an `ADHOC:` id instead of a `DA-2b:` id), Layer A's deterministic-subset filter misses it. Reviewer must spot-check `ADHOC:`-prefixed finding_ids.
2. **Calibration drift vs the baseline** — D2 verifies severity is internally consistent with cited rubric evidence; it does NOT verify that `engineering-baseline.md` itself is calibrated against current best practice. A stale baseline (>90 days, per CLAUDE.md) silently inflates High counts without triggering any pipeline layer. `/refresh-engineering-baseline` is out-of-band.
3. **Report-vs-tool-use-log audit** — D4's URL set is extracted from the report text; verifying each citation was actually resolved in the producing session requires reading the session JSONL under `$HOME/.claude/projects/<project>/<sessionId>.jsonl`. The pipeline does not auto-parse JSONL — Layer B asks the critic to flag obvious reconstructed-from-memory URLs but cannot prove resolution.
4. **Cross-agent activation-collision detection** — D5's RD-3 / activation-collision check relies on the Layer-B critic spotting trigger-phrase overlap between the agent under review and siblings. The pipeline does NOT auto-enumerate sibling agents in the repo and diff trigger phrases. A collision with a sibling that the critic does not have visibility into is a residual gap; spot-check via `grep -h "^description:" agents/*.md .claude/agents/*.md` when reviewing high-risk routing.
5. **Single-file constraint of agents** — agents cannot have reference files, so there is no sidecar-vs-report parity check analogous to review-skill's findings.json sidecar. The certificate is the sole authoritative artifact; if the certificate is corrupted post-Layer-A and pre-Write, no second artifact can reveal the corruption.

The Output report MUST list which residual classes apply when the critic returns any `UNCERTAIN` flags or when `--compare-with` is absent (D1 N/A).

## Phase 4 — Report Persistence (standalone mode only)

In orchestrated mode, skip this phase entirely — return only the structured certificate above.

In standalone mode:
1. Present the certificate to the user.
Before Write: scan the assembled report (frontmatter `target:`, optional `origin:`, and the entire body including per-finding evidence quotations) and replace any literal absolute home-directory prefix with `$HOME/`. The `~/.claude/hooks/block-sensitive-content.sh` PreToolUse hook denies Writes containing such prefixes.
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
- **Tier A tool justification:** Write + WebSearch/WebFetch are present because: (1) Write is restricted to the `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` directory only — never to the analyzed agent path, never outside this report directory, (2) WebSearch is used only for domain research during Phase 2 Step A goal inference, never for file modification (it is a read-only network tool by Anthropic spec), (3) WebFetch is restricted to fetching documentation URLs identified by WebSearch results during the same domain-research step — used only for evidence gathering on Goal Alignment, never for arbitrary URLs, never for file modification, and bounded to a single fetch per review per the resource caps. (4) Bash(bash bin/repo-slug.sh:*) computes the deterministic repo-slug used in report paths. Read and Glob are read-only and need no per-tool binding (SP-2b applies to mutating tools only). The read-only Hard Rule above prevents any write-to-analyzed-agent risk; combined with the Write path restriction, this confines all mutations to the report directory allowlist.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present the full certificate before any follow-up actions.**
