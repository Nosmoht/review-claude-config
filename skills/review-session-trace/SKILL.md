---
name: review-session-trace
description: >
  Analyzes a Claude Code JSONL transcript and produces a structured trace
  report: tool-call distribution, error rates, retry patterns, delegation
  chains, token usage, and behavioral signals mapped to MAST failure modes.
  Use when asked to 'review trace', 'analyze session', or 'audit transcript'.
  Do NOT use for narrow error classification against MAST taxonomy —
  use /classify-trace-errors instead.
argument-hint: <path-to-transcript.jsonl>
allowed-tools: Bash, Read, Write, Glob, Grep
---

# Review Session Trace

You are a trace analysis tool that reads Claude Code JSONL transcripts and produces structured runtime audit reports. Your job is to extract quantitative signals from session data and flag behavioral patterns that indicate reliability risks.

## Argument Handling

- `$ARGUMENTS` is the path to a `.jsonl` transcript file.
- If empty, check `~/.claude/projects/` for recent transcripts and suggest the most recent one. If no transcripts found, ask the user for a path and stop.
- Validate the file exists and the first line parses as JSON with a `uuid` field.
- If the file is not a valid transcript, report the error and stop.

## Termination and Escalation

**Termination conditions (abort with partial report if any is met):**
- Grep returns >1000 matches for any single pattern — cap processing at 500, note truncation in report
- Analysis exceeds 8 sequential tool calls without producing output — emit partial report and stop
- File size >50 MB — report "transcript too large for skill-based analysis" and stop

**Escalation triggers (ask the user before continuing):**
- Transcript first line does not parse as JSON — may be wrong file format
- >10 behavioral patterns detected — session may warrant manual inspection
- Grep returns 0 tool_use matches — transcript may be empty or a non-standard format

## Phase 1 — Parsing

### Step 0: Tool Availability

Verify Grep works by running a trivial pattern on the transcript (e.g., `"uuid"`). If Grep fails, report error and stop — this skill requires Grep for bulk extraction.

### Step 1: Load Schema

Read `references/transcript-schema.md` for the JSONL entry structure.

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)

### Step 2: Sample the Transcript

Read the first 50 lines and the last 20 lines to determine session boundaries (start/end timestamps, session ID, total line count via Grep for line count).

### Steps 3-5: Bulk Extraction (parallelizable — run all Grep calls together)

**Step 3 — Tool calls:** Grep for `"type":\s*"tool_use"` to extract tool names and IDs. Grep for `"type":\s*"tool_result"` to count results and detect failures (content containing `"error"` or `"Error"`).

**Step 4 — Token usage:** Grep for `"input_tokens"` to find usage objects. Sum `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`.

**Step 5 — Delegation:** Grep for `"name":\s*"Agent"` in tool_use blocks to identify subagent spawns. Count delegation depth from nested agent calls.

**Resource caps (hard limits per analysis):** Read ≤200 lines directly (sampling), use Grep for bulk extraction. Do not read the entire transcript into context — transcripts can exceed 100K tokens.

**Error handling for each extraction step:**
- Grep returns 0 matches → record metric as 0, note "no data" in the corresponding output section
- Grep returns error → stop extraction for that metric, continue with remaining steps, note in report
- Read fails (file locked, permission denied) → abort with structured error block
- Truncated transcript (last line is incomplete JSON) → ignore last line, note "transcript appears truncated" in Session Summary

## Phase 2 — Analysis

Steps 6 and 7 require output from Steps 3-5. Step 8 requires output from Steps 6-7.

### Step 6: Compute Metrics

From the extracted data, compute:

| Metric | Method |
|---|---|
| Session duration | Last timestamp - first timestamp |
| Total turns | Count of `type: "assistant"` entries |
| Tool call count by tool | Group tool_use blocks by `name` |
| Tool error rate | tool_results with error content / total results |
| Retry signal | Consecutive tool_use blocks repeated 2 times or more with same `name` in same assistant turn |
| Delegation depth | Max nesting level of Agent tool_use blocks |
| Token totals | Sum of usage fields |
| Cache hit rate | cache_read / (cache_read + input_tokens) |

### Step 7: Behavioral Pattern Detection

Check for these patterns (mapped to MAST failure modes from `research/autonomous-agent-reliability/autonomous-agent-reliability.md`):

| Pattern | Detection Heuristic | MAST Mapping |
|---|---|---|
| Step repetition | Same tool+input called ≥3 times consecutively | FM-1.3 |
| Unbounded retry | Same tool called ≥5 times without different approach | FM-1.5 |
| Premature termination | Session ends with pending tool_use (no matching result) | FM-3.1 |
| No verification | Write/Edit tools used with no subsequent Read/Grep | FM-3.2 |
| Reasoning-action mismatch | Thinking block contains tool name A, next tool_use calls tool B (check first 3 thinking+tool_use pairs that have a tool name in thinking text) | FM-2.6 |
| Context loss signal | Entry with `"compact"` in content, followed within 5 turns by a user prompt substantially similar to one already asked (same tool+input pattern) | FM-1.4 |

Report each detected pattern with: count, example evidence (line number + content excerpt), severity (High/Medium/Low).

### Step 8: Risk Summary

Classify the session:
- **Clean** — 0 behavioral patterns detected, error rate <5%
- **Caution** — 1-2 Low/Medium patterns or error rate 5-15%
- **Concern** — any High pattern or error rate >15% or ≥3 patterns total

## Phase 3 — Output

Return the report in this exact format:

### Status
[clean | caution | concern]

### Session Summary

| Metric | Value |
|---|---|
| Transcript | [filename] |
| Duration | [X min Y sec] |
| Turns | [N] |
| Tool calls | [N] |
| Tool errors | [N] ([X%]) |
| Subagent spawns | [N] (max depth [D]) |

### Tool Call Distribution

| Tool | Count | Errors | Error Rate |
|---|---|---|---|
| [tool_name] | [N] | [N] | [X%] |
| ... | ... | ... | ... |

### Token Usage

| Metric | Value |
|---|---|
| Input tokens | [N] |
| Output tokens | [N] |
| Cache reads | [N] |
| Cache creates | [N] |
| Cache hit rate | [X%] |

### Behavioral Signals

[For each detected pattern:]
- **[Pattern name]** (MAST [FM-X.Y], Severity: [H/M/L]) — [count] occurrences. Example: line [N], [brief evidence excerpt].

[If no patterns: "No behavioral signals detected."]

### Recommendations

[1-3 actionable recommendations based on findings. Reference specific patterns and suggest concrete mitigations.]

## Quality measurement (mandatory between Phase 3 and Phase 4)

Without verification, this skill fails at **F6 — Determinism failure on LLM-judged behavioral signals** (the Step 7 patterns "Reasoning-action mismatch" and "Context loss signal" rely on heuristic phrase pattern-matching against thinking blocks and compact-event proximity; two runs of the same skill on the same JSONL transcript can produce different `behavioral_signals` ledgers — this is the canonical F6 example named in the AUDIT category template, per Acknowledged Residual #3) and at **F9 — Evidence fabrication** (a behavioral-signal entry cites `line N` from the transcript for an excerpt that does not actually appear at that line, polluting High-severity findings with hallucinated line references that masquerade as concrete evidence). The JSONL transcript is structured runtime data — every line-number and excerpt the audit emits is a claim that must round-trip back to the transcript byte-identically.

Run the three layers BEFORE Phase 4 (Report Persistence). Treat the unsigned report draft as `$REPORT`; treat the resolved JSONL transcript path (from Argument Handling) as `$TARGET`. The Layer A excerpt-presence and line-ref checks are the load-bearing F9 defense. The Layer A `token_usage_arithmetic` STRICT row defends against silent inconsistency between the Token Usage table and the Session Summary totals. Sensitive-content sweeps (hardcoded user-home prefixes, RFC1918 IPs) are NOT in Layer A — those are enforced at Write time by the `block-sensitive-content.sh` PreToolUse hook, which is the canonical defense.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024), Beyond Consensus (NUS 2025), `research/autonomous-agent-reliability/autonomous-agent-reliability.md` (MAST FM-X.Y catalog and severity map for behavioral-signal patterns).

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the produced report file. Any non-zero `STRICT` row → abort and report to user; any `SOFT` row delta → log warning, surface in output footnote, do not auto-persist.

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

REQUIRED_FM = ["generated_by", "schema_version", "date", "repo", "target", "summary"]
missing_fm = [k for k in REQUIRED_FM if not re.search(rf"^{k}:", fm, re.M)]

schema_v_m = re.search(r"^schema_version:\s*(\d+)", fm, re.M)
schema_v = int(schema_v_m.group(1)) if schema_v_m else None

STATUS_VOCAB = {"clean", "caution", "concern"}

# Body status: line directly after `### Status` heading
body_status_m = re.search(r"^###\s+Status\s*\n+\[?([a-z\-]+)\]?", body, re.M)
body_status = body_status_m.group(1) if body_status_m else None

# Frontmatter status: `status:` field nested under `summary:` entries
fm_statuses = re.findall(r"^\s+status:\s*([a-z\-|\s]+)$", fm, re.M)
fm_statuses = [s.strip() for s in fm_statuses if s.strip()]

# MAST FM-X.Y rule-id catalog: closed set per references
mast_ids = re.findall(r"\bFM-(\d+)\.(\d+)\b", body)
bad_mast = [f"FM-{a}.{b}" for a, b in mast_ids if int(a) < 1 or int(a) > 3]

# Severity tokens
severities = re.findall(r"Severity:\s*([HML])\b", body)
sev_ok = all(s in {"H", "M", "L"} for s in severities)

# Rule-severity consistency (F8): each FM-X.Y appears with a single severity
sev_per_rule = {}
for m in re.finditer(r"\bFM-(\d+\.\d+)\b[^\n]*?Severity:\s*([HML])", body):
    rid, sv = m.group(1), m.group(2)
    sev_per_rule.setdefault(rid, set()).add(sv)
inconsistent_sev = {f"FM-{k}": sorted(v) for k, v in sev_per_rule.items() if len(v) > 1}

# Token-usage arithmetic (STRICT): sum of components matches stated total when both present
def grab_int(pat):
    m = re.search(pat, body)
    if not m: return None
    try: return int(m.group(1).replace(",", ""))
    except: return None

input_tok = grab_int(r"Input tokens\s*\|\s*([\d,]+)")
output_tok = grab_int(r"Output tokens\s*\|\s*([\d,]+)")
cache_r   = grab_int(r"Cache reads\s*\|\s*([\d,]+)")
cache_c   = grab_int(r"Cache creates\s*\|\s*([\d,]+)")
total_tok = grab_int(r"Total tokens\s*\|\s*([\d,]+)")
tok_arith_ok = True
tok_note = ""
if total_tok is not None and all(v is not None for v in (input_tok, output_tok, cache_r, cache_c)):
    summed = input_tok + output_tok + cache_r + cache_c
    tok_arith_ok = (summed == total_tok)
    tok_note = f"sum={summed} total={total_tok}"

# Cache hit-rate arithmetic (SOFT): cache_reads / (cache_reads + cache_creates) within +/- 0.5%
hit_rate_m = re.search(r"Cache hit rate\s*\|\s*([\d.]+)\s*%", body)
hit_rate_ok = True
hit_note = ""
if hit_rate_m and cache_r is not None and cache_c is not None and (cache_r + cache_c) > 0:
    expected = 100.0 * cache_r / (cache_r + cache_c)
    reported = float(hit_rate_m.group(1))
    hit_rate_ok = abs(expected - reported) <= 0.5
    hit_note = f"expected={expected:.2f}% reported={reported:.2f}%"

# Line-ref → transcript existence (sample up to 5, F9 defense)
line_refs = [int(n) for n in re.findall(r"line\s+(\d+)", body, re.I)]
out_of_range = []
if target_path and os.path.exists(target_path) and line_refs:
    try:
        # cheap line count — do not load full transcript into memory
        with open(target_path) as tf:
            line_count = sum(1 for _ in tf)
        out_of_range = [ln for ln in line_refs[:5] if ln > line_count or ln < 1]
    except Exception:
        out_of_range = []

# Excerpt-presence: sample up to 3 evidence excerpts (F9 defense)
excerpts = re.findall(r"Evidence:[^\n]*?`([^`]+)`", body)
missing_excerpts = []
if target_path and os.path.exists(target_path) and excerpts:
    try:
        with open(target_path) as tf:
            transcript_text = tf.read()
        missing_excerpts = [e for e in excerpts[:3] if e and e not in transcript_text]
    except Exception:
        missing_excerpts = []

# Status consistency (body matches summary[].status)
status_consistent = (
    body_status is not None
    and fm_statuses
    and all(s == body_status for s in fm_statuses)
)

rows = []
def add(sev, name, val, ok, note=""):
    flag = "" if ok else (" FAIL" if sev == "STRICT" else " warn")
    rows.append((sev, name, val, flag, note))

add("STRICT", "frontmatter_present",       "yes", bool(fm_match))
add("STRICT", "required_frontmatter_keys", f"missing={missing_fm}", len(missing_fm) == 0)
add("STRICT", "schema_version_pinned",     f"v{schema_v}", schema_v == 1,
    note="bump invalidates analytics consumers")
add("STRICT", "status_in_vocab_body",      f"chosen={body_status}",
    body_status in STATUS_VOCAB,
    note="closed set {clean, caution, concern}")
add("STRICT", "status_in_vocab_fm",        f"summary_statuses={fm_statuses}",
    all(s in STATUS_VOCAB for s in fm_statuses) if fm_statuses else False)
add("STRICT", "status_consistent",         f"body={body_status} fm={fm_statuses}",
    status_consistent,
    note="body ### Status and summary[].status must agree")
add("STRICT", "mast_id_format",            f"out_of_range={sorted(bad_mast)}",
    len(bad_mast) == 0,
    note="MAST catalog closed at FM-[1-3].N")
add("STRICT", "severity_tokens_valid",     f"set={sorted(set(severities))}", sev_ok)
add("STRICT", "rule_severity_stable",      f"inconsistent={inconsistent_sev}",
    len(inconsistent_sev) == 0,
    note="each FM-X.Y must use a single severity across the report")
add("STRICT", "token_usage_arithmetic",    tok_note or "no-total-reported",
    tok_arith_ok,
    note="input+output+cache_reads+cache_creates must equal stated total")
add("STRICT", "evidence_line_refs_valid",  f"out_of_range={out_of_range}",
    len(out_of_range) == 0,
    note="every cited line N must satisfy 1 <= N <= line_count(transcript) — F9 defense")
add("STRICT", "evidence_excerpts_present", f"missing={missing_excerpts}",
    len(missing_excerpts) == 0,
    note="every cited excerpt must round-trip to the JSONL transcript (F9 defense)")
add("SOFT",   "cache_hit_rate_arithmetic", hit_note or "no-rate-reported",
    hit_rate_ok,
    note="reported rate must match cache_reads / (cache_reads + cache_creates) within +/-0.5%")

# Determinism (SOFT): if env var set, diff rule-id set across two runs
det_path = os.environ.get("DETERMINISM_RUN_2_REPORT")
if det_path and os.path.exists(det_path):
    with open(det_path) as f2: t2 = f2.read()
    rule_ids_2 = set(re.findall(r"\bFM-\d+\.\d+\b", t2))
    rule_ids_1 = set(re.findall(r"\bFM-\d+\.\d+\b", body))
    diff = rule_ids_1 ^ rule_ids_2
    add("SOFT", "determinism_rule_set", f"symmetric_diff={sorted(diff)}",
        len(diff) == 0,
        note="behavioral-signal heuristics are LLM-judged; set may shift across runs")

fail = 0
print(f"{'severity':8} {'metric':30} {'value':32} {'flag':>6}  note")
for sev, name, val, flag, note in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:8} {name:30} {str(val)[:32]:32} {flag:>6}  {note}")
sys.exit(1 if fail else 0)
PY
```

Metric coverage matrix (which failure class each STRICT/SOFT row catches):

| Layer-A row                   | Catches                                |
|-------------------------------|----------------------------------------|
| `frontmatter_present`         | F5 (report shape)                      |
| `required_frontmatter_keys`   | F5                                     |
| `schema_version_pinned`       | F10                                    |
| `status_in_vocab_body`        | F5                                     |
| `status_in_vocab_fm`          | F5 (frontmatter summary[])             |
| `status_consistent`           | F5 (body↔frontmatter drift)            |
| `mast_id_format`              | F4 (FM-X.Y catalog closure)            |
| `severity_tokens_valid`       | F5, F8                                 |
| `rule_severity_stable`        | F8                                     |
| `token_usage_arithmetic`      | F8/F9 (silent arithmetic inconsistency)|
| `evidence_line_refs_valid`    | F9 (hallucinated line numbers)         |
| `evidence_excerpts_present`   | F9 (fabricated excerpts)               |
| `cache_hit_rate_arithmetic` SOFT | F8 (rate-vs-component drift)        |
| `determinism_rule_set` SOFT   | F6 (behavioral-signal LLM-judged)      |

### Layer B — adversarial critic dispatch (blind, recall-framed)

**Layer-B-Gate.** Per `docs/skill-verification-architecture.md`, AUDIT output is structured extraction when predicates are mechanical. Layer B fires when ANY of the following criteria hold for this skill's run:

- (a) The skill's predicate set includes LLM-classified items (closed-set classification, taxonomy mapping, MAST-class assignment, behavioral-signal detection, free-form severity assessment).
- (b) The skill emits free-form prose findings beyond a closed-set predicate match.
- (c) The operator observes judgment-shaped failure modes during a dry-run (false positives traceable to a heuristic, ambiguous classifications, inter-run disagreement).

For purely-mechanical audits (file-exists / regex-match / exit-code only, with no LLM-judged predicates and no free-form prose), skip Layer B and rely on Layer A + Layer C alone. Surface the gate decision in the report under a body heading: `## Layer B (fired: <criterion-met>)` or `## Layer B (skipped: predicates are mechanical)` — do NOT introduce a frontmatter `layer_b_fired` field (no schema-parity treatment defined; surface in body where context is also reported).

Dispatch a fresh subagent. The critic operates on the pair `(JSONL transcript, audit-report)` — NOT on a before/after pair, because the report is derived from a single input. For transcripts >5 KB the prompt pastes the first 2 KB plus sampled middle/end blocks of the transcript (the critic's recall against a sampled view is still useful for surfacing DROPPED patterns on flagged regions).

```
Agent({
  description: "Blind review-session-trace critic (FM-X.Y recall vs precision)",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind audit-critic. You are given two artifacts:\n" +
    "\n" +
    "A: the JSONL session transcript the audit consumed " +
    "(first 2 KB plus sampled middle and end blocks for large files).\n" +
    "B: the audit report that was produced from A, containing a Session " +
    "Summary, Tool Call Distribution, Token Usage, and Behavioral Signals " +
    "ledger with MAST FM-X.Y rule-ids.\n" +
    "\n" +
    "The audit's behavioral-signal catalog is closed at the following MAST " +
    "patterns (per the skill's Step 7 detection table):\n" +
    "  FM-1.3 step repetition (same tool+input >=3 times consecutively)\n" +
    "  FM-1.4 context loss (compact entry then similar prompt within 5 turns)\n" +
    "  FM-1.5 unbounded retry (same tool >=5 times without different approach)\n" +
    "  FM-2.6 reasoning-action mismatch (thinking names tool A, tool_use is B)\n" +
    "  FM-3.1 premature termination (session ends with pending tool_use)\n" +
    "  FM-3.2 no verification (Write/Edit with no subsequent Read/Grep)\n" +
    "\n" +
    "For each finding in B, locate the corresponding evidence in A and " +
    "classify as:\n" +
    "  GROUNDED — evidence in A matches the rule-id and severity asserted.\n" +
    "  WEAKENED — evidence in A is weaker than the rule-id suggests " +
    "(e.g., severity should be Low, report says High).\n" +
    "  ADDED — no evidence in A supports the finding (false positive / " +
    "hallucinated line number or fabricated excerpt).\n" +
    "\n" +
    "Separately, scan A for patterns the report did NOT flag. If you find " +
    "JSONL content that an alert reader would expect to trigger one of " +
    "FM-1.3/1.4/1.5/2.6/3.1/3.2 but no finding cites it, classify as:\n" +
    "  DROPPED — rule that should have fired but did not. Watch especially " +
    "for: (a) DROPPED retry storms (a single tool repeated >=5 times not " +
    "flagged as FM-1.5); (b) DROPPED premature termination (a pending " +
    "tool_use at the end of A not flagged as FM-3.1); (c) DROPPED no-" +
    "verification (Write/Edit followed only by another Write/Edit, no " +
    "Read/Grep before the next user turn).\n" +
    "\n" +
    "Report ONE block per item. Format:\n" +
    "  [GROUNDED|WEAKENED|ADDED|DROPPED]: rule-id (or 'no-rule' for DROPPED)\n" +
    "  evidence_in_A: '<short quote or line N>'\n" +
    "  evidence_in_B: '<short quote or finding-id>'\n" +
    "  reason: <=2 sentences>\n" +
    "\n" +
    "Do not rate report quality. Do not summarize. Report under 500 words.\n" +
    "\n" +
    "A:\n<paste $TARGET sampled contents per the size policy above>\n" +
    "\n" +
    "B:\n<paste $REPORT contents>"
})
```

**Order-swap mandate**: dispatch a second time with artifact labels reversed (A=report, B=transcript). Take the union of items flagged across both runs (de-dup by `rule-id × evidence_in_A`). Position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791).

Output vocabulary maps to Layer C as: `GROUNDED` → no impact; `ADDED` → D2 NO; `WEAKENED` → D4 NO; `DROPPED` → D5 NO.

### Layer C — binary rubric (6 yes/no dimensions)

```
D1 STATUS_VOCAB_CONFORMANT   Body `### Status` value AND every
                              summary[].status in frontmatter both
                              belong to {clean, caution, concern}.
                              Body status and frontmatter statuses
                              agree (no drift between the two surfaces).
                              Catches F5.

D2 EVIDENCE_GROUNDED          Every Behavioral-Signal finding's `line N`
                              reference satisfies 1 <= N <= line_count(
                              transcript), AND every cited `Evidence:`
                              excerpt round-trips to the JSONL transcript
                              byte-identically (Layer A line-ref + excerpt
                              checks passed AND no Layer-B ADDED items).
                              The load-bearing dimension for this skill
                              per the AUDIT category template's per-skill
                              note. Catches F2, F9.

D3 TAXONOMY_DISJOINT          No two findings cite distinct FM-X.Y rule-
                              ids for the same evidence span; the MAST
                              FM-X.Y catalog is closed at FM-1.N, FM-2.N,
                              FM-3.N (out-of-range IDs → NO). Catches F4.

D4 SEVERITY_CALIBRATED        Each FM-X.Y appears with a single severity
                              across the report, AND that severity
                              matches the documented severity in the
                              Step 7 detection table (High/Medium/Low
                              per pattern). No Layer-B WEAKENED items
                              survive. The Token Usage table arithmetic
                              also holds (input+output+cache_reads+
                              cache_creates equals stated total when
                              total reported). Catches F8.

D5 RULE_CATALOG_COMPLETENESS  Layer-B critic surfaced ZERO `DROPPED`
                              items — every documented behavioral
                              pattern (FM-1.3/1.4/1.5/2.6/3.1/3.2) that
                              fires in the transcript has a corresponding
                              finding. DROPPED retry storms, DROPPED
                              premature termination, and DROPPED no-
                              verification are the load-bearing recall
                              failures this dimension catches.
                              Catches F1, F3.

D6 DISCOVERY_PRECISION        Trivially YES for this skill — review-
                              session-trace is predicate-class, not
                              discovery-class. The FM-X.Y catalog is
                              fixed; no candidate-skill ledger or
                              intervention-matrix emission. Per AUDIT
                              template Layer C definition,
                              "for predicate-class output: trivially
                              YES." Catches F7 (n/a here).
```

Layer-A row → Dimension mapping:
- `status_in_vocab_body`, `status_in_vocab_fm`, `status_consistent` → D1
- `frontmatter_present`, `required_frontmatter_keys`, `schema_version_pinned` → D1
- `evidence_line_refs_valid`, `evidence_excerpts_present` → D2
- `mast_id_format` → D3
- `severity_tokens_valid`, `rule_severity_stable`, `token_usage_arithmetic` → D4
- `cache_hit_rate_arithmetic` SOFT → D4 (warn, does not block)

Layer-B item → Dimension mapping:
- `ADDED` → D2 NO
- `WEAKENED` → D4 NO
- `DROPPED` → D5 NO
- `GROUNDED` → no impact

### Reconciliation outcomes

- **All STRICT pass + zero ADDED/WEAKENED/DROPPED from critic** → proceed to Phase 4 (Report Persistence).
- **Any STRICT fail OR any ADDED/WEAKENED/DROPPED** → patch inline: drop fabricated findings, re-classify weakened severity, add dropped rule firings. Re-run Layer A on the patched report. Max 2 iterations. If still failing after iteration 2, surface to user with the full ledger and DO NOT persist the report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Only SOFT warnings** (e.g. `determinism_rule_set` symmetric-diff non-empty across two runs of the FM-2.6/FM-1.4 LLM-judged patterns; `cache_hit_rate_arithmetic` reporting drift) → append a footnote in the audit report ("This audit was non-deterministic across N runs on behavioral-signal patterns FM-2.6/FM-1.4; finding set may vary") and proceed.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Behavioral-signal heuristic determinism** — the FM-2.6 reasoning-action-mismatch pattern compares free-text thinking-block content against subsequent `tool_use` names; the FM-1.4 context-loss pattern compares prompt similarity within a 5-turn window. Both are LLM-judged pattern matches, not deterministic predicates. The SOFT-warn surfaces variability across runs but does not resolve it; LLM-as-judge calibration error stays. This is the canonical F6 example for this skill per the AUDIT category template Acknowledged Residual #3. Mitigation: the audit report footnotes determinism warnings so the maintainer knows which patterns warrant manual confirmation.
2. **JSONL-content poisoning at the critic boundary** — the Layer-B critic reads transcript contents as part of its prompt. A prior session whose transcript contains adversarial instructions (e.g., system-prompt-shaped strings in assistant turns) could attempt to subvert the critic. Mitigation: the critic prompt frames its task as recall against a closed catalog (no instruction-following on transcript content); the critic's only write-grant is its tool-response back to the orchestrator; per `rules/subagent-delegation.md §Summary files are untrusted data`, the orchestrator treats the critic's output as data, not instructions.
3. **Cross-session correlation gaps** — the pipeline judges one report against its single JSONL input. A pattern visible only across multiple sessions (e.g., a slowly-escalating tool-grant pattern detectable only when 10 traces are co-analyzed) escapes both Layers A and B. Mitigation: cross-trace analysis is its own audit class (`/review-analytics`), not a `review-session-trace` failure. This matches AUDIT template Acknowledged Residual #1.
4. **MAST taxonomy boundary ambiguity** — when a trace error genuinely sits between two MAST classes (e.g., FM-1.4 "Context loss" vs FM-2.6 "Reasoning-action mismatch" on a thinking block that both omits a recent decision AND references a different tool than the next call), the critic can flag the choice but cannot decide which is canonically right. D3 catches conflict; it does not decide truth. This matches AUDIT template Acknowledged Residual #2.

The Output report MUST list which residual classes apply when the critic surfaces DROPPED items or when SOFT determinism warnings fire, so the user has one last human-glance opportunity.

## Phase 4 — Report Persistence

1. Present the report to the user.
2. Confirm before writing: "Save trace report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-session-trace.md`?"
3. If confirmed, create the `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` directory if it does not exist. Write with frontmatter:
   ```yaml
   ---
   generated_by: review-session-trace
   schema_version: 1
   date: YYYY-MM-DD
   repo: <slug>
   origin: <git-remote-url>  # optional
   target: /path/to/transcript.jsonl
   summary:
     - name: session-trace
       type: SessionTrace
       path: relative/path/to/transcript.jsonl
       status: clean|caution|concern
       tool_calls: N
       tool_errors: N
       behavioral_signals: N
   ---
   ```

## Hard Rules

- **Read-only on the transcript.** Never modify the analyzed file. Write only to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Tier A justification:** Write is for report persistence only. Grep/Read are for transcript parsing. No web tools needed.
- **Context budget discipline.** Do not read the full transcript into context. Use Grep for bulk extraction, Read with offset/limit for sampling. Transcripts can be 100K+ tokens.
- **Evidence over inference.** Report only patterns with concrete line-number evidence. Do not speculate about intent.
- **Present the full report before any follow-up actions.**

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
