---
name: review-hook
description: >
  Evaluates a hooks.json entry + Python script across 5 dimensions (Clarity,
  Completeness, Goal Alignment, Safety, Metadata). Use when asked to 'review
  hook' or after /develop-hooks. Do NOT use for skills or agents.
argument-hint: <path-to-hooks.json or path-to-hook-script.py>
allowed-tools: Bash, Read, Write, Glob, WebSearch, WebFetch
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

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)

**If any of these files is not found, abort with error:** "Required reference not found. Ensure review-claude-config is installed as a sibling skill."

Read the type-specific evaluation guide from this skill's own directory:
- `references/hook-evaluation-guide.md`

## Phase 2 — Evaluation

### Step A: Hook Purpose Inference

1. Read `hooks.json` and all referenced Python scripts.
2. Identify: event type(s), matcher scope (if any), and stated purpose from the `description` field or filename.
3. State the hook's purpose in one sentence: "This hook [does X] when [event Y] fires [on Z]."

### Step B: Domain Research

Check the domain cache: Read `${CLAUDE_PLUGIN_ROOT}/skills/review-claude-config/references/domain-cache/INDEX.md` and match to a universal cache entry.
- If `CACHED` (≤90 days): use cache as primary knowledge.
- If `STALE`: perform 1 WebSearch to refresh.
- If no cache entry matches: perform 1-2 targeted WebSearch queries for Claude Code hook quality patterns (technology + workflow aspect, not generic "best practices"). Fetch the top result if `webfetch_available`.
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

## Quality measurement (mandatory before Phase 4)

Without verification, this skill fails at DIMENSION-GRADE-ABSENCE (a report omits the Safety or Goal-Alignment dimension grade silently — emitting an empty row or a non-applicable PE/CE grade — instead of `null` per `references/review-report-contract.md` §"Dimensions: Hooks: non-applicable PE/CE → null"), MISSING-SAFETY (the Python script touches sensitive paths like `.ssh`, `.kube`, `*.env`, or `credentials.*` and the report fails to flag a `Safety` finding — SR-1 / PY-4 territory in `references/hook-evaluation-guide.md`), and TYPE-MISMATCH (the skill is dispatched on a non-hook artifact — a SKILL.md or agent .md — and proceeds to emit a 5-dim Hook certificate instead of stopping; or hooks.json is reviewed without reading its referenced Python scripts, producing a half-unit assessment). The three-layer pipeline below catches all three.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), `references/review-report-contract.md`, `references/scoring-rubric.md` §6 "Safety weighting for hooks", `references/hook-evaluation-guide.md`.

Run the pipeline against the assembled Phase 3 certificate. Compute `REPORT_PATH` as the path the Phase 4 step 3 Write will use; if no path is available yet (orchestrated mode), serialize the certificate to a tempfile for the duration of this section.

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the assembled report. STRICT failures block Phase 4; SOFT warnings surface in Output.

```bash
python3 - "$REPORT_PATH" "${HOOKS_JSON_PATH:-}" "${PY_SCRIPT_PATHS:-}" <<'PY'
import sys, re, os
from pathlib import Path

REPORT = Path(sys.argv[1])
HJ     = sys.argv[2]            # hooks.json path under review (may be "")
PYS    = sys.argv[3].split(":") if sys.argv[3] else []  # ":"-joined Python script paths

SEVERITY_VOCAB = {"High","Medium","Low"}
DIM_SET_HOOK   = {"clarity","completeness","goal_alignment","safety","metadata"}
DIM_NULL_HOOK  = {"prompt_engineering","context_engineering"}
GRADE_VOCAB    = {"A","B","C","D","F"}
URL_RE   = r"https?://[^\s)`\"<>]+"
CITE_RE  = r"\b(arXiv:[0-9.]+|RFC\s*[0-9]+|DOI:[^\s)]+)"
FIND_RE  = r"^####\s+\d+\.\s+.+\(Impact:\s*(High|Medium|Low)"
FM_RE    = r"\A---\n(.*?)\n---\n"
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
if gb and gb.group(1) != "review-hook":
    errors.append(f"STRICT: generated_by must be 'review-hook', got '{gb.group(1)}'")
typ = re.search(r"\btype\s*:\s*(\S+)", fm)
if typ and typ.group(1).rstrip(",") != "Hook":
    errors.append(f"STRICT: summary[].type must be 'Hook', got '{typ.group(1)}'")
if HOME_RE.search(fm):
    errors.append("STRICT: frontmatter 'target' uses expanded home prefix; must use literal $HOME/")

sections = [s.group(1).strip() for s in re.finditer(r"^##\s+(.+)$", text, re.M)]
order = ["Goal","Certificate","Strengths","Recommendations"]
pos = {k: next((i for i,s in enumerate(sections) if s.startswith(k)), -1) for k in order}
if any(v == -1 for v in pos.values()):
    errors.append(f"STRICT: missing required section heading from {order}; found={sections}")
elif sorted(pos.values()) != list(pos.values()):
    errors.append("STRICT: section order violates Goal->Certificate->Strengths->Recommendations")

for dim in DIM_SET_HOOK:
    mm = re.search(rf"\b{dim}\s*:\s*(\S+)", fm)
    if not mm:
        errors.append(f"STRICT: summary missing required Hook dimension '{dim}'")
        continue
    v = mm.group(1).rstrip(",")
    if v not in GRADE_VOCAB and v != "null":
        errors.append(f"STRICT: dimension {dim}='{v}' not in {{A,B,C,D,F,null}}")
for dim in DIM_NULL_HOOK:
    mm = re.search(rf"\b{dim}\s*:\s*(\S+)", fm)
    if mm:
        v = mm.group(1).rstrip(",")
        if v != "null":
            errors.append(f"STRICT: non-applicable dim {dim}='{v}' must be 'null' for Hook type")

findings = re.findall(FIND_RE, text, re.M)
for sev in findings:
    if sev not in SEVERITY_VOCAB:
        errors.append(f"STRICT: finding severity '{sev}' not in {SEVERITY_VOCAB}")
blocks = re.split(r"^####\s+\d+\.", text, flags=re.M)[1:]
for i, b in enumerate(blocks, 1):
    for sub in ["Evidence","Why it matters","Validation"]:
        if not re.search(rf"\b{sub}\b", b):
            errors.append(f"STRICT: finding #{i} missing required sub-block '{sub}'")

# Hook-unit completeness: both hooks.json AND >=1 Python script must be cited in Evidence
hj_basename = os.path.basename(HJ) if HJ else "hooks.json"
py_basenames = [os.path.basename(p) for p in PYS if p]
hj_cited = bool(re.search(rf"\b{re.escape(hj_basename)}\b", text))
py_cited = any(re.search(rf"\b{re.escape(n)}\b", text) for n in py_basenames) if py_basenames else True
if not hj_cited:
    errors.append(f"STRICT: report does not cite hooks.json basename '{hj_basename}' — hook-unit incomplete")
if PYS and not py_cited:
    errors.append(f"STRICT: report does not cite any Python script from {py_basenames} — hook-unit incomplete (PY-* dimension undocumented)")

urls  = set(re.findall(URL_RE,  text))
cites = set(c if isinstance(c,str) else c[0] for c in re.findall(CITE_RE, text))
warns.append(f"INFO: urls={len(urls)} cites={len(cites)} (Layer B verifies resolution)")

print(f"=== Layer A — {REPORT.name} ===")
for w in warns:  print(f"warn  {w}")
for e in errors: print(f"FAIL  {e}")
print(f"--- {len(errors)} STRICT, {len(warns)} SOFT ---")
sys.exit(1 if errors else 0)
PY
```

What each metric catches: frontmatter required-fields + `$HOME/` literal → DIMENSION-GRADE-ABSENCE and the `block-sensitive-content.sh` PreToolUse contract; `type` field equals `Hook` → TYPE-MISMATCH; section order → structural validity; 5-dim coverage (Clarity, Completeness, Goal Alignment, Safety, Metadata) + null-enforcement on PE/CE → DIMENSION-GRADE-ABSENCE and TYPE-MISMATCH (a Skill report misclassified as Hook would carry grades on PE/CE); severity vocabulary + finding sub-blocks → SEVERITY-MISCALIBRATION (form-level only); hook-unit citation check (hooks.json basename + ≥1 referenced Python script appear in report text) → HOOK-PAIR completeness (the skill MUST process both inputs per `Hard Rules` §"Evaluate the full hook unit"); URL/cite extraction → CITATION-ROT (Layer B verifies).

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent whose ONLY task is to find what the report MISSED, FABRICATED, or MIS-CLASSIFIED versus the hook unit under review. The critic receives TWO artifact inputs (hooks.json + the referenced Python scripts) and ONE report; adversarial framing is load-bearing — non-adversarial dispatch loses MISSING-SAFETY and CITATION-ROT recall.

```
Agent({
  description: "Adversarial review-hook report critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer. Three inputs are attached: HOOKS_JSON, " +
    "PY_SCRIPTS, and REPORT. The first two together form the ARTIFACT " +
    "(a hook unit — a hooks.json entry plus all referenced Python " +
    "scripts). REPORT is the review certificate emitted by /review-hook.\n\n" +
    "Your only task is to find what the REPORT got wrong. List every " +
    "item that meets one of:\n" +
    "- MISSING — a defect actually present in the ARTIFACT (hooks.json " +
    "  OR any Python script) that REPORT does not flag (cite the file " +
    "  + line, name the dimension it violates: Clarity, Completeness, " +
    "  Goal Alignment, Safety, Metadata).\n" +
    "- MISSING-SAFETY — a Safety defect specifically: the Python script " +
    "  reads/writes a sensitive path (`.ssh`, `.kube`, `*.env`, " +
    "  `credentials.*`, `/etc/`), uses `exit 0` for a blocking decision " +
    "  on a PreToolUse hook, lacks a top-level exception handler, or " +
    "  spawns network I/O without timeout — and REPORT does not flag it.\n" +
    "- MISSING-EVENT-MISMATCH — hooks.json declares an event that does " +
    "  not fire on the trigger the description claims (e.g., " +
    "  PostToolUse for a 'block on bad input' hook that should be " +
    "  PreToolUse) and REPORT does not flag it.\n" +
    "- FABRICATED — a finding in REPORT whose claimed Evidence quote " +
    "  does not appear verbatim in hooks.json or any Python script " +
    "  (cite finding heading + absent quote).\n" +
    "- MIS-SEVERITY — a finding whose severity (High|Medium|Low) is " +
    "  inconsistent with its evidence per the rubric grade caps " +
    "  (Safety High requires a credential leak, sandbox escape, or " +
    "  silent block-bypass; Goal Alignment High requires wrong event " +
    "  or wrong matcher; mismatches must be re-rated).\n" +
    "- MIS-CITED — a URL, arXiv ID, RFC, or `references/*.md` citation " +
    "  in REPORT that reads as reconstructed-from-memory rather than " +
    "  resolved-in-session (broken link, wrong file, no tool-response).\n" +
    "- UNCITED — a quantitative or evidence-based claim in REPORT with " +
    "  no citation at all.\n" +
    "- HALF-UNIT — REPORT cites hooks.json but never quotes from any " +
    "  Python script (or vice versa) when the ARTIFACT contains both. " +
    "  The skill's Hard Rule requires evaluating the full hook unit.\n\n" +
    "Do not rate quality. Do not praise. Do not propose fixes. List " +
    "items only. Quote the literal sentence and name which file. " +
    "Report under 500 words.\n\n" +
    "HOOKS_JSON:\n<paste hooks.json contents>\n\n" +
    "PY_SCRIPTS:\n<paste each referenced Python script's contents>\n\n" +
    "REPORT:\n<paste certificate contents>"
})
```

**Dispatch twice with order swapped** (ARTIFACT↔REPORT label position) — position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791). Take the union of items flagged across both runs.

### Layer C — binary rubric reconciliation

Six binary dimensions, each yes/no, each tied to ≥1 failure class. Any `NO` blocks Phase 4 until resolved.

```
D1 HOOK_UNIT_COMPLETE     Both hooks.json AND every referenced Python script
                          are quoted (Evidence block contains a literal line
                          from each file in the unit). No HALF-UNIT Layer-B
                          item open. If hooks.json references N scripts, at
                          least N-1 of them appear in Evidence (one may be
                          implicitly NA when no PY-* failure exists in it).
                          (Catches: HOOK-PAIR incompleteness, TYPE-MISMATCH
                          where a SKILL.md was reviewed as a hook)

D2 SAFETY_JUSTIFIED       Every finding's severity matches its evidence per
                          the rubric §"Grade Caps"; Safety dimension weighted
                          per `scoring-rubric.md` §6 (25% weight for hooks);
                          no Layer-B MIS-SEVERITY or MISSING-SAFETY item
                          open. A Safety-High finding cites a credential
                          path, sandbox escape, or block-bypass — not a
                          stylistic preference.
                          (Catches: SEVERITY-MISCALIBRATION, MISSING-SAFETY)

D3 DIMENSION_COVERAGE     All 5 dimensions for Hook type (Clarity,
                          Completeness, Goal Alignment, Safety, Metadata)
                          appear in summary[] with grade in {A,B,C,D,F};
                          non-applicable dimensions (prompt_engineering,
                          context_engineering) are `null`, not absent and
                          not graded.
                          (Catches: DIMENSION-GRADE-ABSENCE, TYPE-MISMATCH)

D4 EVIDENCE_RESOLVED      Every URL, arXiv ID, RFC, and `references/*.md`
                          path cited in REPORT was either resolved in the
                          producing session (verifiable from tool-use log)
                          OR carries an explicit `[no web verification]` /
                          `[unverified-url]` marker; no MIS-CITED or UNCITED
                          Layer-B item open. Goal Alignment dimension
                          explicitly marked `[no web verification]` when
                          `websearch_available=false`.
                          (Catches: CITATION-ROT, UNCITED)

D5 NO_FABRICATED_FINDINGS Every finding's Evidence block contains a literal
                          quote from the analyzed hooks.json or one of its
                          Python scripts; no FABRICATED Layer-B item open;
                          quoted line numbers match the source file.
                          (Catches: SEVERITY-MISCALIBRATION false-positive
                          class, FABRICATED)

D6 EVENT_MATCHER_SCOPED   Goal Alignment evidence verifies hooks.json
                          declares an event in the 26-event catalog with
                          a matcher that is single-tool or explicit-glob
                          (not a catch-all); no MISSING-EVENT-MISMATCH
                          Layer-B item open. When hook runtime type is
                          `prompt`, `http`, or `agent`, timeout is
                          documented in the Completeness evidence.
                          (Catches: Goal-Alignment scope drift, event
                          mismatch, matcher over-breadth)
```

Map Layer-A failures → D1/D3/D4. Map Layer-B `MISSING` / `MISSING-SAFETY` / `FABRICATED` → D5 (or D2 for MISSING-SAFETY specifically). Map `MIS-SEVERITY` → D2. Map `MIS-CITED` / `UNCITED` → D4. Map `HALF-UNIT` → D1. Map `MISSING-EVENT-MISMATCH` → D6.

### Reconciliation outcomes

- **All Layer-A STRICT pass + zero Layer-B `MISSING`/`MISSING-SAFETY`/`FABRICATED`/`HALF-UNIT`/`MISSING-EVENT-MISMATCH`** → proceed to Phase 4.
- **Any Layer-A STRICT fail OR any of those Layer-B classes** → propose restorations inline (name each finding to add/remove with the artifact line + rubric citation), re-run Layer A on the patched report. Max two iterations. If still failing at iteration 2, surface to user and do NOT auto-write the report.
- **Only Layer-A SOFT warnings + Layer-B `MIS-SEVERITY` / `MIS-CITED` / `UNCITED` items** → record in Phase 4 Output under `### Layer-B Findings (Advisory)` and proceed. These do not block ship; reviewer triages.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Calibration drift vs the baseline** — D2 verifies severity is internally consistent with cited rubric evidence; it does NOT verify that `engineering-baseline.md` or `hook-evaluation-guide.md` is calibrated against current Claude Code hook event catalog. A stale guide (>90 days, per CLAUDE.md) silently mis-grades hooks using post-v2.1.x events (e.g., `PostToolUseFailure`, `CwdChanged`). `/refresh-engineering-baseline` and HC-1's `scripts/verify_hook_events.py` are out-of-band.
2. **Report-vs-tool-use-log audit** — D4's URL set is extracted from the report text; verifying each citation was actually resolved in the producing session requires reading the session JSONL under `$HOME/.claude/projects/<project>/<sessionId>.jsonl`. The pipeline does not auto-parse JSONL — Layer B asks the critic to flag obvious reconstructed-from-memory URLs but cannot prove resolution.
3. **Runtime hook-input semantics** — D6 verifies the hook event is in the 26-event catalog and matcher is scoped, but does NOT execute the hook to verify it actually fires on the expected input shape. A hook that declares `PreToolUse` with matcher `Edit` may still parse `sys.stdin` incorrectly and block legitimate Edits at runtime; static review cannot catch this. End-to-end verification requires running `claude --plugin-dir` against a fixture.
4. **Multi-script hook units with cross-script dependencies** — D1's hook-unit-complete check requires Evidence quotes from each referenced Python script, but does NOT verify cross-script invariants (e.g., script A writes a state file that script B reads). The pipeline accepts isolated per-script evaluation as a valid path.

The Output report MUST list which residual classes apply when the critic returns any `UNCERTAIN` flags.

## Phase 4 — Report Persistence (standalone mode only)

In orchestrated mode, skip this phase entirely — return only the structured certificate above.

In standalone mode:
1. Present the certificate to the user.
2. Confirm before writing: "Save review report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-hook.md`?"
3. If confirmed, assemble the report using the canonical frontmatter contract with:
   - `generated_by: review-hook`
   - one `summary` item of type `Hook`
   - non-applicable dimensions (PE, CE) set to `null`
   - `repo: <slug>` and optionally `origin: <git-remote-url>`
   - `type + path` as the canonical identity and `name` as display-only
4. Write the report file. Suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report`
5. **What's Next?**

After all output is complete, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Apply findings manually" (Recommended) — description: `"Address High/Medium findings using the Current/Recommended blocks; hook code changes (hooks.json + Python scripts) require manual review before edit"`
- Option 2 label: "Review another hook" — description: `"Provide a hook path to review next"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Apply findings manually": list the High/Medium findings with their Current/Recommended blocks for the user to act on. On "Review another hook": ask for the hook path, then invoke `/review-hook`. On "Done": acknowledge and stop.

## Error Handling

On evaluation failure, return a structured error block:

```
## ERROR
{item_path}: {reason}
```

In orchestrated mode, the orchestrator logs this and continues with remaining items.

## Hard Rules

- **Read-only on the analyzed hook files.** Never modify hooks.json or Python scripts being reviewed. Write only to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite.**
- **Present the full certificate before any follow-up actions.**
- **Evaluate the full hook unit** (hooks.json entry + all referenced scripts). Do not score hooks.json alone.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
