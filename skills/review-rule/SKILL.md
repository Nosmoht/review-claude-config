---
name: review-rule
description: >
  Evaluates a single rule .md (always-load imperatives, injection-prone
  prose) across 3 dimensions (Clarity, Completeness, Goal Alignment). Use
  when asked to 'review rule' or dispatched by /review-claude-config. Do
  NOT use for skills or agents — use /review-skill or /review-agent.
argument-hint: <path-to-rule.md>
allowed-tools: Bash, Read, Write, Glob, WebSearch, WebFetch
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

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)

**If any of these files is not found, abort with error:** "Required reference not found. Ensure review-claude-config is installed as a sibling skill."

Read the type-specific evaluation guide from this skill's own directory:
- `references/rule-evaluation-guide.md`

## Phase 2 — Evaluation

### Step A: Goal Inference + Domain Research

1. Read the rule file and infer its primary constraint/goal in one sentence.
2. Domain research (follow orchestration flags if in orchestrated mode):
   - First, check the domain cache: Read `${CLAUDE_PLUGIN_ROOT}/skills/review-claude-config/references/domain-cache/INDEX.md` and match the rule's domain to a universal cache entry.
   - If `CACHED` (entry exists, ≤90 days old): read the cache file and use as primary domain knowledge. At most 1 supplemental WebSearch query if the cache lacks coverage for this rule's specific area.
   - If `STALE` (≥90 days): perform 1 WebSearch query to refresh.
   - If no cache entry matches: extract domain keywords from the rule's content, then perform 1-2 targeted WebSearch queries (technology + workflow + quality aspect, not generic "best practices"). If `webfetch_available`, fetch the most relevant URL.
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

## Quality measurement (mandatory before Phase 4)

Without verification, this skill fails at TYPE-MISMATCH (a SKILL.md or agent .md is passed in and the skill produces a 3-dimension Rule certificate instead of stopping), DIMENSION-GRADE-ABSENCE (the rule-specific subset omits a dimension grade silently or emits a non-applicable dimension at non-null value, contradicting `references/review-report-contract.md` §"Dimensions: Rules/MCP/Settings: non-applicable → null"), and IMPLICIT-DIRECTIVE-LOSS-IN-EVIDENCE (the rule body is imperative-heavy prose — Bell 1984 recipient-design markers, von Fintel 1994 scope qualifiers, Kratzer conditional frames — and the Evidence block summarises rather than quotes verbatim, weakening the finding's force without altering its surface meaning per `~/.claude/skills/reword-skill/SKILL.md §Preserve`). The three-layer pipeline below catches all three.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (Jiang et al. ACL 2024), Beyond Consensus (NUS 2025), `skills/review-claude-config/references/review-report-contract.md`, `skills/review-claude-config/references/scoring-rubric.md`, `skills/review-rule/references/rule-evaluation-guide.md`.

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
RULE_DIMS      = {"clarity","completeness","goal_alignment"}
NA_DIMS        = {"prompt_engineering","context_engineering","safety","metadata"}
GRADE_VOCAB    = {"A","B","C","D","F"}
URL_RE   = r"https?://[^\s)`\"<>]+"
CITE_RE  = r"\b(arXiv:[0-9.]+|RFC\s*[0-9]+|DOI:[^\s)]+)"
FIND_RE  = r"^####\s+\d+\.\s+.+\(Impact:\s*(High|Medium|Low)"
FM_RE    = r"\A---\n(.*?)\n---\n"
ID_RE    = r"ID:\s*([A-Z][A-Z0-9-]+:[^,\s)]+/v1)"
# Catch frontmatter target: lines beginning with an absolute tilde-expanded
# user-home prefix on either supported POSIX layout. Live regex form
# matches the literal prefixes; placeholdered in this SKILL.md so the
# PreToolUse content-block hook does not reject this Write.
HOME_RE  = re.compile(r"^target\s*:\s*/(?:Users|home)/[^/\s]+/", re.M)

errors, warns = [], []
text = REPORT.read_text()
m = re.match(FM_RE, text, re.S)
if not m:
    errors.append("STRICT: report missing YAML frontmatter")
    print("\n".join(errors)); sys.exit(1)
fm = m.group(1)

for k in ["generated_by","schema_version","date","repo","target","items_reviewed"]:
    if not re.search(rf"^{k}\s*:", fm, re.M):
        errors.append(f"STRICT: frontmatter missing required field '{k}'")
gb = re.search(r"^generated_by\s*:\s*(\S+)", fm, re.M)
if gb and gb.group(1) != "review-rule":
    errors.append(f"STRICT: generated_by must be 'review-rule', got '{gb.group(1)}'")
if HOME_RE.search(fm):
    errors.append("STRICT: frontmatter 'target' uses expanded home prefix; must use literal $HOME/")

typ = re.search(r"\btype\s*:\s*(\w+)", fm)
if typ and typ.group(1) != "Rule":
    errors.append(f"STRICT: summary type must be 'Rule', got '{typ.group(1)}' (TYPE-MISMATCH — wrong skill dispatched)")

sections = [s.group(1).strip() for s in re.finditer(r"^##\s+(.+)$", text, re.M)]
order = ["Goal","Certificate","Strengths","Recommendations"]
pos = {k: next((i for i,s in enumerate(sections) if s.startswith(k)), -1) for k in order}
if any(v == -1 for v in pos.values()):
    errors.append(f"STRICT: missing required section heading from {order}; found={sections}")
elif sorted(pos.values()) != list(pos.values()):
    errors.append("STRICT: section order violates Goal->Certificate->Strengths->Recommendations")

for dim in RULE_DIMS:
    mm = re.search(rf"\b{dim}\s*:\s*(\S+)", fm)
    if not mm:
        errors.append(f"STRICT: summary missing required Rule dimension '{dim}'")
        continue
    v = mm.group(1).rstrip(",")
    if v not in GRADE_VOCAB:
        errors.append(f"STRICT: Rule dimension {dim}='{v}' not in {{A,B,C,D,F}}")
for dim in NA_DIMS:
    mm = re.search(rf"\b{dim}\s*:\s*(\S+)", fm)
    if mm:
        v = mm.group(1).rstrip(",")
        if v != "null":
            errors.append(f"STRICT: non-applicable dimension '{dim}'='{v}' must be 'null' for type=Rule")

findings = re.findall(FIND_RE, text, re.M)
for sev in findings:
    if sev not in SEVERITY_VOCAB:
        errors.append(f"STRICT: finding severity '{sev}' not in {SEVERITY_VOCAB}")
blocks = re.split(r"^####\s+\d+\.", text, flags=re.M)[1:]
for i, b in enumerate(blocks, 1):
    for sub in ["Evidence","Why it matters","Validation"]:
        if not re.search(rf"\b{sub}\b", b):
            errors.append(f"STRICT: finding #{i} missing required sub-block '{sub}'")

urls  = set(re.findall(URL_RE,  text))
cites = set(c if isinstance(c,str) else c[0] for c in re.findall(CITE_RE, text))
warns.append(f"INFO: urls={len(urls)} cites={len(cites)} (Layer B verifies resolution)")

if PRIOR and os.path.exists(PRIOR):
    prior = json.loads(Path(PRIOR).read_text())
    cur = set(re.findall(ID_RE, text))
    prev = {f["finding_id"] for f in prior.get("findings",[])
            if f.get("severity") in {"High","Medium"}}
    drift = cur ^ prev
    if drift:
        errors.append(f"STRICT: convergence drift on H+M finding_ids: lost={sorted(prev-cur)} gained={sorted(cur-prev)}")

print(f"=== Layer A — {REPORT.name} ===")
for w in warns:  print(f"warn  {w}")
for e in errors: print(f"FAIL  {e}")
print(f"--- {len(errors)} STRICT, {len(warns)} SOFT ---")
sys.exit(1 if errors else 0)
PY
```

What each metric catches: frontmatter required-fields + `$HOME/` literal → DIMENSION-GRADE-ABSENCE and the `block-sensitive-content.sh` PreToolUse contract; section order → structural validity; `type=Rule` check → TYPE-MISMATCH (skill or agent passed where rule expected); rule-dim-presence + na-dim-null-only → DIMENSION-GRADE-ABSENCE and the report-contract Rule-subset constraint; severity vocabulary + finding sub-blocks → SEVERITY-MISCALIBRATION (form-level only); convergence diff against prior `merged.json` → CONVERGENCE-DRIFT.

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent whose ONLY task is to find what the report MISSED, FABRICATED, or MIS-CLASSIFIED versus the rule .md under review. Adversarial framing is load-bearing — non-adversarial dispatch loses CITATION-ROT and implicit-directive-loss recall.

```
Agent({
  description: "Adversarial review-rule report critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer. Two markdown files are attached: ARTIFACT " +
    "and REPORT. Neither label tells you which is which until you read " +
    "them. ARTIFACT is the rule .md under review (a Claude Code rule — " +
    "always-load imperative prose, typically under .claude/rules/ or " +
    "~/.claude/rules/, with no standardized frontmatter). REPORT is the " +
    "review certificate emitted by /review-rule.\n\n" +
    "Your only task is to find what the REPORT got wrong. List every " +
    "item that meets one of:\n" +
    "- MISSING — a defect actually present in ARTIFACT that REPORT does " +
    "  not flag (cite the line, name the rubric dimension it violates: " +
    "  Clarity, Completeness, or Goal Alignment).\n" +
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
    "- TYPE-MISMATCH — REPORT scored ARTIFACT as a Rule but ARTIFACT " +
    "  has SKILL.md frontmatter (a `name:` field) or agent frontmatter " +
    "  (`model:` / `tools:`) — wrong skill dispatched; review should " +
    "  have stopped.\n" +
    "- IMPLICIT-DIRECTIVE-LOSS — Evidence block paraphrases an " +
    "  imperative sentence from ARTIFACT in a way that drops its force: " +
    "  audience specifier ('to the user'), temporal qualifier " +
    "  ('currently'), scope qualifier ('in this repo'), conditional " +
    "  frame ('when X'), intensifier ('actively'), or curt one-word " +
    "  imperative ('Use JSON.'). Per reword-skill §Preserve.\n" +
    "- NA-DIMENSION-LEAK — REPORT emits a non-null grade for a " +
    "  dimension outside {Clarity, Completeness, Goal Alignment} (must " +
    "  be `null` for Rule type per review-report-contract.md).\n\n" +
    "Do not rate quality. Do not praise. Do not propose fixes. List " +
    "items only. Quote the literal sentence and name which file. Report " +
    "under 500 words.\n\n" +
    "ARTIFACT:\n<paste rule .md contents>\n\n" +
    "REPORT:\n<paste certificate contents>"
})
```

**Dispatch twice with order swapped** (ARTIFACT↔REPORT label position) — position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791). Take the union of items flagged across both runs.

### Layer C — binary rubric reconciliation

Six binary dimensions, each yes/no, each tied to ≥1 failure class. Any `NO` blocks Phase 4 until resolved.

```
D1 CONVERGENCE_STABILITY  When a prior merged.json for this rule is supplied,
                          the set of finding_id values at severity in {High,
                          Medium} is byte-identical between runs. When no
                          prior is supplied, D1 is N/A (declared as such in
                          Output; not a NO).
                          (Catches: CONVERGENCE-DRIFT)

D2 SEVERITY_JUSTIFIED     Every finding's severity matches its evidence per
                          the rubric §"Grade Caps" + rule-evaluation-guide
                          checklist (CL-1..CL-N, COMP-1..COMP-N, GA-1..GA-N);
                          no Layer-B MIS-SEVERITY item open. Severity bound
                          only to the three applicable dimensions (Clarity,
                          Completeness, Goal Alignment).
                          (Catches: SEVERITY-MISCALIBRATION)

D3 DIMENSION_COVERAGE     Exactly the 3-dim Rule subset {clarity,
                          completeness, goal_alignment} appears in summary[]
                          with grade in {A,B,C,D,F}; the 4 non-applicable
                          dimensions {prompt_engineering, context_engineering,
                          safety, metadata} are present with value `null` or
                          omitted per contract — never carry a letter grade;
                          summary[].type == "Rule"; no Layer-B
                          NA-DIMENSION-LEAK or TYPE-MISMATCH item open.
                          (Catches: DIMENSION-GRADE-ABSENCE, TYPE-MISMATCH)

D4 EVIDENCE_RESOLVED      Every URL, arXiv ID, RFC, and references/*.md path
                          cited in REPORT was either resolved in the
                          producing session (verifiable from tool-use log)
                          OR carries an explicit `[no web verification]` /
                          `[unverified-url]` marker; no MIS-CITED or UNCITED
                          Layer-B item open.
                          (Catches: CITATION-ROT, UNCITED)

D5 NO_FABRICATED_FINDINGS Every finding's Evidence block contains a literal
                          verbatim quote from the analyzed rule .md (not a
                          paraphrase that drops force); no FABRICATED,
                          FALSE-RESOLUTION, or IMPLICIT-DIRECTIVE-LOSS
                          Layer-B item open.
                          (Catches: FABRICATION, FALSE-FIX-PASS,
                          IMPLICIT-DIRECTIVE-LOSS-IN-EVIDENCE)

D6 SCOPE_DISCIPLINE       Phase 4 writes only under
                          ${HOME}/.claude/plugins/data/claude-config/reports/
                          <repo-slug>/; the rule .md under review is
                          never modified; per Hard Rules "Read-only on the
                          analyzed rule". No finding cites a dimension
                          outside the Rule subset.
                          (Catches: scope creep, dim-leak)
```

Map Layer-A failures → D3/D4. Map Layer-B `MISSING` / `FABRICATED` → D5. Map `MIS-SEVERITY` → D2. Map `MIS-CITED` / `UNCITED` → D4. Map `FALSE-RESOLUTION` / `IMPLICIT-DIRECTIVE-LOSS` → D5. Map `TYPE-MISMATCH` / `NA-DIMENSION-LEAK` → D3.

### Reconciliation outcomes

- **All Layer-A STRICT pass + zero Layer-B `MISSING`/`FABRICATED`/`FALSE-RESOLUTION`/`TYPE-MISMATCH`/`NA-DIMENSION-LEAK`/`IMPLICIT-DIRECTIVE-LOSS`** → proceed to Phase 4.
- **Any Layer-A STRICT fail OR any of those Layer-B classes** → propose restorations inline (name each finding to add/remove with the artifact line + rubric citation), re-run Layer A on the patched report. Max two iterations. If still failing at iteration 2, surface to user and do NOT auto-write the report.
- **Only Layer-A SOFT warnings + Layer-B `MIS-SEVERITY` / `MIS-CITED` / `UNCITED` items** → record in Phase 4 Output under `### Layer-B Findings (Advisory)` and proceed. These do not block ship; reviewer triages.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Calibration drift vs the baseline** — D2 verifies severity is internally consistent with the rubric's cited grade caps; it does NOT verify that `engineering-baseline.md` itself is calibrated against current best practice. A stale baseline (>90 days, per CLAUDE.md) silently inflates High counts without triggering any pipeline layer. `/refresh-engineering-baseline` is out-of-band.
2. **Report-vs-tool-use-log audit** — D4's URL set is extracted from the report text; verifying each citation was actually resolved in the producing session requires reading the session JSONL under `$HOME/.claude/projects/<project>/<sessionId>.jsonl`. The pipeline does not auto-parse JSONL — Layer B asks the critic to flag obvious reconstructed-from-memory URLs but cannot prove resolution.
3. **Cross-rule coherence** — a finding that recommends rewording rule-A may break an unstated assumption in rule-B (e.g., a sibling rule cites the literal phrase being rewritten); the pipeline reviews one rule in isolation. No corpus-level coherence evaluator is implemented here. Reviewer must spot-check `Recommended:` blocks against any sibling rule that grep-references the original phrase.
4. **Pragmatic / illocutionary force in the rule body itself** — `~/.claude/skills/reword-skill/SKILL.md §Preserve` acknowledges that curt-imperative force is invisible to NLI. The /review-rule report Evidence block can quote the curt imperative verbatim and pass D5 even when the finding's `Recommended:` rewrite weakens the force. Only register-aware human review catches this on the Recommended side.
5. **Checklist-item soundness** — the rule-evaluation-guide encodes per-checklist-item PASS/FAIL rules (CL-1..CL-N, COMP-1..COMP-N, GA-1..GA-N); D2 verifies the *cited* checklist verdict is consistent with the severity, NOT that the verdict itself is correct on the artifact. A poisoned or stale `rule-evaluation-guide.md` propagates silently.

The Output report MUST list which residual classes apply when the critic returns any `UNCERTAIN` flags or when `--compare-with` is absent (D1 N/A).

## Phase 4 — Report Persistence (standalone mode only)

In orchestrated mode, skip this phase entirely — return only the structured certificate above.

In standalone mode:
1. Present the certificate to the user.
Before Write: scan the assembled report (frontmatter `target:`, optional `origin:`, and the entire body including per-finding evidence quotations) and replace any literal absolute home-directory prefix with `$HOME/`. The `~/.claude/hooks/block-sensitive-content.sh` PreToolUse hook denies Writes containing such prefixes.
2. Confirm before writing: "Save review report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-rule.md`?"
3. If confirmed, assemble the report using the canonical frontmatter contract located in Step 1 with:
   - `generated_by: review-rule`
   - one `summary` item of type `Rule`
   - non-applicable dimensions set to `null`
   - `repo: <slug>` and optionally `origin: <git-remote-url>`
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

- **Read-only on the analyzed rule.** Never modify the rule being reviewed. Write only to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present the full certificate before any follow-up actions.**
- **Use only 3 dimensions.** Never score rules on PE, CE, Safety, or Metadata.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
