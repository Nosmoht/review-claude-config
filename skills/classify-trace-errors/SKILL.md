---
name: classify-trace-errors
description: >
  Classifies errors in a Claude Code audit trace or transcript JSONL against
  the MAST failure taxonomy. Outputs a structured error classification report
  with severity, evidence, and remediation guidance. Use when asked to
  'classify errors', 'analyze failures', or 'categorize trace errors'.
  Do NOT use for full session-trace review or behavioral-pattern analysis —
  use /review-session-trace instead.
argument-hint: <path-to-trace.jsonl>
allowed-tools: Bash, Read, Write, Glob, Grep
---

# Classify Trace Errors

You are an error classification tool that reads Claude Code audit traces or transcripts and maps observed patterns to the MAST failure taxonomy. Your job is to produce a structured report that categorizes runtime failures by type and severity.

## Argument Handling

- `$ARGUMENTS` is a path to a `.jsonl` file (audit trace or raw transcript).
- If empty, check `${HOME}/.claude/plugins/data/claude-config/audit/` for recent audit traces. If none found, ask the user for a path and stop.
- Validate the file exists and contains parseable JSONL.

## Termination and Escalation

**Termination conditions:**
- Grep returns >1000 matches for any pattern — cap at 500, note truncation
- >8 sequential tool calls without output — emit partial report and stop

**Escalation triggers (ask user):**
- File does not contain tool_use entries — may not be a session trace
- >20 distinct failure codes detected — session may need manual triage

## Phase 1 — Load References

### Step 1: Load Taxonomy

Read `references/failure-taxonomy.md` for the codebook (MAST failure modes, detection heuristics, severity levels).

### Step 2: Detect Trace Format

Read the first 10 lines. Determine format:
- **Audit trace** — entries have `"type": "tool_call"` (produced by observation hooks)
- **Raw transcript** — entries have `"message"` with `"content"` blocks (native Claude Code JSONL)

Set format flag for parsing logic below.

## Phase 2 — Pattern Detection (Steps 3-8 are parallelizable — run all Grep calls together)

**Resource caps:** Read ≤100 lines directly, use Grep for bulk extraction.

### Step 3: Detect FM-1.3 (Step Repetition)

Grep for all tool_use entries. Identify sequences where the same tool_name + input appears ≥3 times consecutively. For audit traces: same `tool_name` + `input_hash`. For transcripts: same `"name"` field in consecutive `tool_use` blocks.

### Step 4: Detect FM-1.5 (Unaware of Termination)

Count total tool calls. If >200 with no session_summary or stop signal, flag.

### Step 5: Detect FM-2.6 (Reasoning-Action Mismatch)

For raw transcripts only: Grep for `"type": "thinking"` entries. For each, check if the next `tool_use` block's tool name appears in the thinking text. Flag mismatches for the first 5 instances found.

### Step 6: Detect FM-3.1 (Premature Termination)

Check last 20 lines. If the final assistant entry contains a `tool_use` block with no matching `tool_result` in subsequent entries, flag.

### Step 7: Detect FM-3.2 (No Verification)

Grep for Write/Edit tool calls. For each, check whether a Read or Grep call targeting the same path appears within the next 10 entries. Flag unverified writes.

### Step 8: Detect FM-1.4 (Context Loss)

Grep for compaction signals (`"compact"` or `"type": "system"`). If found, check subsequent 10 entries for tool patterns that duplicate earlier patterns.

**Error handling:** If Grep returns 0 for any pattern, record that failure mode as "not detected" (count: 0). If Grep fails, skip that detection and note in report.

Step 9 requires output from Steps 3-8.

### Step 9: Aggregate and Classify

For each detected pattern, produce a classification entry per the schema in the taxonomy codebook. Sort by severity (High → Medium → Low), then by count.

Compute summary:
- Total failure modes detected
- High/Medium/Low counts
- Dominant failure category (FC1/FC2/FC3)

## Phase 3 — Output

### Status
[clean | caution | concern]
- `clean` — 0 failures detected
- `caution` — only Low/Medium failures
- `concern` — any High failure

### Classification Summary

| Category | Failures | Dominant Mode |
|---|---|---|
| FC1 — Specification | [N] | [FM-X.Y] |
| FC2 — Misalignment | [N] | [FM-X.Y] |
| FC3 — Verification | [N] | [FM-X.Y] |
| **Total** | **[N]** | |

### Detected Failures

[For each failure, ordered by severity:]

#### FM-X.Y: [Name] (Severity: [H/M/L], Count: [N])
**Evidence:** Line [N]: `[excerpt]`
**Remediation:** [Specific fix recommendation]

[If no failures: "No failure modes detected in this trace."]

### Recommendations

[1-3 actionable recommendations targeting the dominant failure category.]

## Quality measurement (mandatory before Phase 4 — Report Persistence)

Without verification, this skill fails at **F4 — Classification taxonomy ambiguity** (the same trace error can plausibly map to two MAST classes; canonical example: a tool call after compaction that duplicates an earlier pattern fits both FM-1.4 "Context loss" and FM-2.6 "Reasoning-Action mismatch"; the critic can flag the boundary case but cannot decide which is canonically right — surface, do not silently resolve) and at **F1 — Predicate incompleteness** (the closed FM-1.1..FM-3.3 catalog misses a defect class present in the trace; e.g., FM-1.1 "Disobey task spec" and FM-1.2 "Disobey role spec" are listed in `references/failure-taxonomy.md` but have no Phase 2 detector — Layer B surfaces these as `DROPPED`). D3 TAXONOMY_DISJOINT is load-bearing for this skill: a single trace error mapped to two distinct FM-X.Y identifiers within one report is a STRICT-fail per Layer C. D2 EVIDENCE_GROUNDED (every cited `Line N` excerpt is resolvable in the trace JSONL) and D5 RULE_CATALOG_COMPLETENESS (zero `DROPPED` items from Layer B) are the other two load-bearing dimensions.

Run the three layers BEFORE Phase 4 Step 2 (Confirm before writing). Treat the unsigned report drafted in Phase 3 as `$REPORT`; treat the analyzed trace JSONL as `$TARGET`. Sensitive-content sweeps (hardcoded user-home prefixes, RFC1918 IPs) are NOT in Layer A — those are enforced at Write time by the `block-sensitive-content.sh` PreToolUse hook, which is the canonical defense; duplicating the regex here would itself violate the doc-content constraint.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024), Beyond Consensus (NUS 2025), MAST (arXiv:2503.13657), `references/failure-taxonomy.md` (closed FM-1.1..FM-3.3 catalog with documented severities), `skills/review-claude-config/references/signal-catalog.md` (catalog-completeness reasoning for D5).

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the produced report. Any non-zero `STRICT` row → abort and report; any `SOFT` row delta → log warning, surface in output footnote, do not auto-persist.

```bash
python3 - "$REPORT" "$TARGET" <<'PY'
import re, sys, os
report_path = sys.argv[1]
target_path = sys.argv[2] if len(sys.argv) > 2 else None

with open(report_path) as f: t = f.read()

# parse frontmatter
fm_match = re.match(r"^---\n(.*?)\n---\n", t, re.S)
if not fm_match:
    print("FAIL STRICT frontmatter_present: no YAML frontmatter detected")
    sys.exit(1)
fm = fm_match.group(1)
body = t[fm_match.end():]

REQUIRED_FM = ["generated_by", "schema_version", "date", "target", "summary"]
missing_fm = [k for k in REQUIRED_FM if not re.search(rf"^{k}:", fm, re.M)]

schema_v_m = re.search(r"^schema_version:\s*(\d+)", fm, re.M)
schema_v = int(schema_v_m.group(1)) if schema_v_m else None

STATUS_VOCAB = {"clean", "caution", "concern"}
nxt = re.search(r"^###?\s+Status\s*\n+\[?[\w\-| ]+\]?\s*\n+([\w\-]+)",
                body, re.M)
status_pick = nxt.group(1) if nxt else None
if not status_pick:
    s_inline = re.search(r"^###?\s+Status\s*\n+([\w\-]+)\s*$", body, re.M)
    status_pick = s_inline.group(1) if s_inline else None

# FM identifier format — closed catalog FM-[1-3].N
fm_ids = re.findall(r"\bFM-(\d+)\.(\d+)\b", t)
out_of_catalog = [f"FM-{a}.{b}" for a, b in fm_ids if int(a) < 1 or int(a) > 3]

# severities
severities = re.findall(r"Severity:\s*([HML])\b", t)
sev_ok = all(s in {"H", "M", "L"} for s in severities)

# documented severity per FM rule (references/failure-taxonomy.md)
DOC_SEVERITY = {
    "FM-1.1": "H", "FM-1.2": "H", "FM-1.3": "M", "FM-1.4": "M", "FM-1.5": "H",
    "FM-2.1": "M", "FM-2.3": "M", "FM-2.6": "M",
    "FM-3.1": "H", "FM-3.2": "M", "FM-3.3": "M",
}
sev_per_rule = {}
for m in re.finditer(r"\b(FM-\d+\.\d+)\b[^\n]*?Severity:\s*([HML])", t):
    sev_per_rule.setdefault(m.group(1), set()).add(m.group(2))
inconsistent = {k: sorted(v) for k, v in sev_per_rule.items() if len(v) > 1}
miscalibrated = {k: (sorted(v), DOC_SEVERITY.get(k))
                 for k, v in sev_per_rule.items()
                 if k in DOC_SEVERITY and sorted(v) != [DOC_SEVERITY[k]]}

# taxonomy-disjoint check: the same Line-N evidence span must not be cited
# by two distinct FM ids in one report (the F4 ambiguity case)
line_to_rules = {}
for m in re.finditer(r"\b(FM-\d+\.\d+)\b[\s\S]{0,200}?Line\s+(\d+)", t):
    line_to_rules.setdefault(m.group(2), set()).add(m.group(1))
double_mapped = {ln: sorted(rs) for ln, rs in line_to_rules.items()
                 if len(rs) > 1}

# evidence: Line N references resolve in target JSONL
line_refs = re.findall(r"Line\s+(\d+)", t)
out_of_range_lines = []
if target_path and os.path.exists(target_path) and line_refs:
    with open(target_path) as tf:
        target_lines = tf.readlines()
    out_of_range_lines = [ln for ln in line_refs[:5]
                          if int(ln) > len(target_lines)]

# summary arithmetic: high+medium+low must equal total_failures
total_m = re.search(r"total_failures:\s*(\d+)", fm)
high_m = re.search(r"^\s*high:\s*(\d+)", fm, re.M)
med_m = re.search(r"^\s*medium:\s*(\d+)", fm, re.M)
low_m = re.search(r"^\s*low:\s*(\d+)", fm, re.M)
arith_ok = True
arith_note = ""
if total_m and high_m and med_m and low_m:
    tot = int(total_m.group(1))
    hml = int(high_m.group(1)) + int(med_m.group(1)) + int(low_m.group(1))
    arith_ok = (tot == hml)
    arith_note = f"total={tot} h+m+l={hml}"

# determinism (SOFT): if env var set, diff FM-rule-id set
det_path = os.environ.get("DETERMINISM_RUN_2_REPORT")
det_diff = None
if det_path and os.path.exists(det_path):
    with open(det_path) as f2: t2 = f2.read()
    rids1 = set(re.findall(r"\bFM-\d+\.\d+\b", t))
    rids2 = set(re.findall(r"\bFM-\d+\.\d+\b", t2))
    det_diff = sorted(rids1 ^ rids2)

rows = []
def add(sev, name, val, ok, note=""):
    flag = "" if ok else (" FAIL" if sev == "STRICT" else " warn")
    rows.append((sev, name, val, flag, note))

add("STRICT", "frontmatter_present",       "yes", bool(fm_match))
add("STRICT", "required_frontmatter_keys", f"missing={missing_fm}",
    len(missing_fm) == 0)
add("STRICT", "schema_version_pinned",     f"v{schema_v}", schema_v == 1,
    note="bump invalidates analytics consumers")
add("STRICT", "status_in_vocab",           f"chosen={status_pick}",
    status_pick in STATUS_VOCAB if status_pick else False,
    note="status must be clean|caution|concern")
add("STRICT", "mast_id_format",            f"out_of_catalog={out_of_catalog}",
    len(out_of_catalog) == 0,
    note="every FM-X.Y must satisfy FM-[1-3].N per failure-taxonomy.md")
add("STRICT", "severity_tokens_valid",     f"set={sorted(set(severities))}",
    sev_ok)
add("STRICT", "rule_severity_stable",      f"inconsistent={inconsistent}",
    len(inconsistent) == 0,
    note="one FM rule must carry one severity across the report")
add("STRICT", "rule_severity_calibrated",  f"miscalibrated={miscalibrated}",
    len(miscalibrated) == 0,
    note="severity must match references/failure-taxonomy.md")
add("STRICT", "taxonomy_disjoint",         f"double_mapped={double_mapped}",
    len(double_mapped) == 0,
    note="one trace line must not be cited by two distinct FM-X.Y ids (F4)")
add("STRICT", "summary_arithmetic",        arith_note or "fields missing",
    arith_ok,
    note="frontmatter high+medium+low must equal total_failures")
if target_path and os.path.exists(target_path):
    add("STRICT", "evidence_line_refs_valid",
        f"out_of_range={out_of_range_lines}",
        len(out_of_range_lines) == 0,
        note="every cited Line N must exist in the trace JSONL")
if det_diff is not None:
    add("SOFT", "determinism_rule_set",
        f"symmetric_diff={det_diff}", len(det_diff) == 0,
        note="LLM-judged boundary cases may shift the FM-rule set across runs")

fail = 0
print(f"{'severity':8} {'metric':32} {'value':30} {'flag':>6}  note")
for sev, name, val, flag, note in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:8} {name:32} {str(val)[:30]:30} {flag:>6}  {note}")
sys.exit(1 if fail else 0)
PY
```

Metric coverage matrix (which failure class each STRICT row catches):

| Layer-A row                       | Catches                |
|-----------------------------------|------------------------|
| `frontmatter_present`             | F5 (report shape)      |
| `required_frontmatter_keys`       | F5                     |
| `schema_version_pinned`           | F10                    |
| `status_in_vocab`                 | F5 (enum drift)        |
| `mast_id_format`                  | F4, F5 (taxonomy drift)|
| `severity_tokens_valid`           | F5, F8                 |
| `rule_severity_stable`            | F8                     |
| `rule_severity_calibrated`        | F8 (vs documented map) |
| `taxonomy_disjoint`               | F4 (load-bearing)      |
| `summary_arithmetic`              | F8/F9 (count drift)    |
| `evidence_line_refs_valid`        | F9 (fabrication)       |
| `determinism_rule_set` (SOFT)     | F6 (LLM judgment)      |

### Layer B — adversarial critic dispatch (blind, recall-framed)

**Layer-B-Gate.** Per `docs/skill-verification-architecture.md`, AUDIT
output is structured extraction when predicates are mechanical. Layer B
fires ONLY when ≥30% of this skill's predicates require LLM judgment
(closed-set classification, taxonomy ambiguity, behavioral-signal
detection). For pure-mechanical audits (file exists / regex matches /
exit code only), SKIP Layer B and rely on Layer A + Layer C alone.
Document the gate decision in the report frontmatter as
`layer_b_fired: true|false (rationale)`.

Dispatch a fresh subagent. The critic operates on the pair `(trace JSONL, classification report)`. The FM-1.1..FM-3.3 catalog is closed (per `references/failure-taxonomy.md`); the critic's job is to find rule firings the classifier MISSED or that it ADDED without justification, with explicit attention to the FM-1.4 (Context loss) vs FM-2.6 (Reasoning-Action mismatch) boundary case where the same evidence can plausibly map to either class.

```
Agent({
  description: "Blind classify-trace-errors critic (FM-X.Y recall)",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind classification-critic. You are given two artifacts:\n" +
    "\n" +
    "A: a Claude Code audit trace or transcript JSONL (entries with " +
    "tool_use, tool_result, thinking, or system events).\n" +
    "B: a classification report containing a Classification Summary " +
    "table (FC1/FC2/FC3 counts) and a Detected Failures list with " +
    "rule-ids in the MAST FM-X.Y closed catalog:\n" +
    "  FC1 — Specification/Design: FM-1.1 (Disobey task spec, H), " +
    "FM-1.2 (Disobey role spec, H), FM-1.3 (Step repetition, M), " +
    "FM-1.4 (Context loss, M), FM-1.5 (No termination, H).\n" +
    "  FC2 — Misalignment: FM-2.1 (Conversation reset, M), " +
    "FM-2.3 (Task derailment, M), FM-2.6 (Reasoning-Action mismatch, M).\n" +
    "  FC3 — Verification/Termination: FM-3.1 (Premature termination, H)," +
    " FM-3.2 (No verification, M), FM-3.3 (Wrong verification, M).\n" +
    "\n" +
    "1. For each finding in B, locate the corresponding evidence in A " +
    "and classify:\n" +
    "   GROUNDED — evidence in A matches the FM rule-id AND the " +
    "asserted severity is the documented one.\n" +
    "   WEAKENED — evidence in A is weaker than the rule-id suggests " +
    "(e.g., severity asserted as H but evidence supports M; or FM-1.3 " +
    "flagged on 2 consecutive identical calls when the heuristic " +
    "requires ≥3).\n" +
    "   ADDED — no evidence in A supports the finding (e.g., cited " +
    "Line N absent from trace; FM-1.5 flagged when total tool calls " +
    "≤200).\n" +
    "\n" +
    "2. Scan A for signal patterns the report did NOT flag. The " +
    "catalog covers heuristics in references/failure-taxonomy.md. If " +
    "you find a passage in A that an alert reader would expect to " +
    "trigger one of FM-1.1..FM-3.3 but no finding cites it, classify " +
    "as:\n" +
    "   DROPPED — rule that should have fired but did not.\n" +
    "\n" +
    "3. Watch specifically for the canonical boundary case: a tool " +
    "call after a `compact` event that duplicates an earlier pattern " +
    "— this fits both FM-1.4 (Context loss) and FM-2.6 " +
    "(Reasoning-Action mismatch). If the report cites only one but " +
    "the other is also defensible, surface as a separate item:\n" +
    "   AMBIGUOUS — single evidence span fits two FM ids; the report " +
    "must surface the alternative, not silently pick one.\n" +
    "\n" +
    "Report ONE block per item. Format:\n" +
    "  [GROUNDED|WEAKENED|ADDED|DROPPED|AMBIGUOUS]: FM-X.Y " +
    "(or 'no-rule' for catalog-gap DROPPED; or 'FM-A.B|FM-C.D' for " +
    "AMBIGUOUS)\n" +
    "  evidence_in_A: '<short quote or jsonl line ref>'\n" +
    "  evidence_in_B: '<short quote or finding-id>'\n" +
    "  reason: <≤2 sentences>\n" +
    "\n" +
    "Do not rate report quality. Do not summarize. Report under 500 " +
    "words.\n" +
    "\n" +
    "A:\n<paste $TARGET; for traces >5KB paste first 2KB + sampled " +
    "middle/end blocks plus all compact/system events>\n" +
    "\n" +
    "B:\n<paste $REPORT contents>"
})
```

**Order-swap mandate**: dispatch a second time with artifact labels reversed (A=report, B=trace JSONL). Take the union of items flagged across both runs (de-dup by `rule-id × evidence_in_A`). Position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791).

Output vocabulary maps to Layer C as: `GROUNDED` → no impact; `ADDED` → D2 NO; `WEAKENED` → D4 NO; `DROPPED` (FM-X.Y in catalog) → D5 NO; `DROPPED` (`no-rule` / catalog-gap) → D5 NO with explicit meta-finding ("catalog needs extension"); `AMBIGUOUS` → D3 NO (per Acknowledged Residual #2, surface both candidates; the pipeline cannot decide canonically right — the report MUST list both FM ids in the same finding with an "alternative classification" note rather than silently pick one).

### Layer C — binary rubric (6 yes/no dimensions)

```
D1 STATUS_VOCAB_CONFORMANT    The `### Status` line and the
                              `summary[].status` frontmatter field both
                              hold a value in the closed set
                              {clean, caution, concern}. Frontmatter
                              schema_version is the pinned value. Catches
                              F5, F10.

D2 EVIDENCE_GROUNDED          Every FM-X.Y finding cites a concrete
                              `Line N` AND an excerpt resolvable in
                              $TARGET (Layer A line-ref check passed
                              AND no Layer-B ADDED items). FM-3.1 and
                              FM-3.2 may cite absence rather than a
                              positive excerpt per Hard Rules; that
                              exemption is encoded in the report's
                              evidence field rather than skipped here.
                              Catches F2, F9.

D3 TAXONOMY_DISJOINT          No two findings cite distinct FM-X.Y
                              rule-ids for the same evidence span (same
                              `Line N`). Every cited rule satisfies
                              FM-[1-3].N per references/failure-
                              taxonomy.md. Layer-B AMBIGUOUS items
                              require the report to surface BOTH
                              candidates in one finding (not two
                              competing findings); a single span mapped
                              to two distinct findings is a STRICT-fail.
                              Catches F4.

D4 SEVERITY_CALIBRATED        Each FM rule appears with a single
                              severity across the report; that severity
                              matches the documented map (FM-1.1=H,
                              FM-1.2=H, FM-1.3=M, FM-1.4=M, FM-1.5=H,
                              FM-2.1=M, FM-2.3=M, FM-2.6=M, FM-3.1=H,
                              FM-3.2=M, FM-3.3=M per references/
                              failure-taxonomy.md). No Layer-B
                              WEAKENED items survive. Catches F8.

D5 RULE_CATALOG_COMPLETENESS  Layer-B critic surfaced ZERO `DROPPED`
                              items. Every documented FM-X.Y that the
                              trace evidence supports must appear in
                              the report at least once. `no-rule` /
                              catalog-gap DROPPED items (e.g., a
                              defect class with no Phase 2 detector
                              such as FM-1.1/FM-1.2 evidence) surface
                              a meta-finding; the catalog itself or the
                              detector set needs extension and the
                              report MUST flag the gap explicitly.
                              Catches F1, F3.

D6 DISCOVERY_PRECISION        Trivially YES — classify-trace-errors
                              emits predicate-class classifications
                              only (FM-1.1..FM-3.3); no heuristic
                              discovery surface. Catches F7 (vacuously).
```

Layer-A row → Dimension mapping:
- `frontmatter_present`, `required_frontmatter_keys`, `schema_version_pinned`, `status_in_vocab` → D1
- `evidence_line_refs_valid`, `summary_arithmetic` → D2
- `mast_id_format`, `taxonomy_disjoint` → D3
- `severity_tokens_valid`, `rule_severity_stable`, `rule_severity_calibrated` → D4

Layer-B item → Dimension mapping:
- `ADDED` → D2 NO
- `WEAKENED` → D4 NO
- `DROPPED` (FM-X.Y) → D5 NO
- `DROPPED` (`no-rule` / catalog-gap) → D5 NO + meta-finding footnote
- `AMBIGUOUS` → D3 NO unless the report restructures the finding to surface BOTH FM ids in one entry (per Acknowledged Residual #2)
- `GROUNDED` → no impact

### Reconciliation outcomes

- **All STRICT pass + zero ADDED/WEAKENED/DROPPED/AMBIGUOUS** → proceed to Phase 4 (Report Persistence).
- **Any STRICT fail OR any ADDED/WEAKENED/DROPPED** → patch inline: drop fabricated findings, recalibrate severities against the documented map, add dropped rule firings. Re-run Layer A on the patched report. Max 2 iterations. If still failing after iteration 2, surface to user with the full ledger and DO NOT persist the report to `${HOME}/.claude/plugins/data/claude-config/reports/`.
- **Any AMBIGUOUS item** → restructure the affected finding to list BOTH candidate FM ids with an "alternative classification" note; do NOT silently pick one. The boundary case (FM-1.4 vs FM-2.6 after compaction) is the canonical example. Re-run Layer A; if `taxonomy_disjoint` still fails, surface to user.
- **Only SOFT warnings** (e.g., `determinism_rule_set` symmetric-diff non-empty) → append a footnote ("This classification was non-deterministic across runs; FM-rule set may vary at boundary cases") and proceed.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **MAST taxonomy ambiguity at the boundary** — the canonical F4 case for this skill. FM-1.4 "Context loss" and FM-2.6 "Reasoning-Action mismatch" share evidence patterns when a tool call after compaction duplicates an earlier pattern AND the thinking text named a different tool. The critic surfaces this as `AMBIGUOUS`; D3 enforces that the report lists both candidates in one finding. The pipeline cannot decide which is canonically right — surface, do not silently resolve.
2. **Detector-set gap vs. catalog gap** — FM-1.1 "Disobey task spec" and FM-1.2 "Disobey role spec" are documented in `references/failure-taxonomy.md` but have no Phase 2 detector step. Layer B will surface evidence for these as `DROPPED` against the catalog (D5 NO) even though the catalog itself is complete. The fix is a detector extension, not a catalog extension; the report MUST distinguish the two in the Recommendations section.
3. **LLM-judged boundary cases** — phrase-pattern detection in FM-2.6 (does the thinking text name tool A while the next call is tool B?) is irreducibly judgment-based. The `determinism_rule_set` SOFT-warn surfaces variability but does not resolve it; LLM-as-judge calibration error stays.
4. **Cross-trace correlation gaps** — the pipeline judges one report against its single trace. A pattern visible only across multiple sessions (e.g., progressive context-loss escalation across 10 sessions) escapes both Layers A and B. Mitigation: cross-trace analysis is `/review-analytics`'s remit, not this skill's.

The Output report MUST list which residual classes apply when the critic surfaces `AMBIGUOUS` or `no-rule` DROPPED items or when SOFT determinism warnings fire, so the user has one last human-glance opportunity.

## Phase 4 — Report Persistence

1. Present the report.
2. Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)
3. Confirm before writing to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-classify-trace-errors.md`.
4. Frontmatter:
   ```yaml
   ---
   generated_by: classify-trace-errors
   schema_version: 1
   date: YYYY-MM-DD
   repo: <slug>
   origin: <git-remote-url>    # Optional
   target: /path/to/trace.jsonl
   summary:
     - name: trace-classification
       type: TraceClassification
       path: relative/path/to/trace.jsonl
       status: clean|caution|concern
       total_failures: N
       high: N
       medium: N
       low: N
   ---
   ```

## Hard Rules

- **Read-only on the trace.** Never modify the analyzed file. Write only to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Tier A justification:** Write is for report persistence only. No web tools needed.
- **Evidence over inference.** Every classification must cite a line number and excerpt. Do not classify based on absence alone except for FM-3.1 and FM-3.2.
- **Taxonomy-only codes.** Only use FM-* codes from the codebook. Do not invent new failure modes.
- **Present the full report before any follow-up actions.**

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
