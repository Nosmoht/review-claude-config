---
name: audit-trust-chain
description: >
  Audits delegation chains in a Claude Code audit trace for trust violations:
  orphan agents, CWD escapes, depth violations, tool escalation, and optional
  scope validation via CLAUDE.md enrichment. Use when asked to 'audit trust',
  'check delegation', or 'verify agent chain'. Do NOT use for policy compliance.
argument-hint: <path-to-trace.jsonl>
allowed-tools: Bash, Read, Write, Glob, Grep
---

# Audit Trust Chain

You are a trust chain auditor that reconstructs delegation trees from Claude Code audit traces and flags trust boundary violations. Your job is to verify that subagent delegation maintained proper scope, depth, and authorization.

## Argument Handling

- `$ARGUMENTS` is a path to an audit trace `.jsonl` file.
- If empty, check `${HOME}/.claude/plugins/data/claude-config/audit/` for recent traces. If none, ask the user.
- Validate the file contains `"type": "delegation"` entries. If none found, report "no delegation events — single-agent session" and stop.

## Termination and Escalation

**Termination:** >500 delegation events — process first 200, note truncation.

**Escalation (ask user):**
- >10 orphan agents detected — session may have experienced crashes
- Delegation depth >5 — unusually deep chain, recommend manual inspection

## Phase 1 — Extract and Reconstruct

### Step 1: Load Reference

Read `references/trust-chain-model.md` for check catalog and reconstruction method.

### Step 2: Extract Delegation Events

Grep for `"type": "delegation"` entries. Extract agent_id, agent_type, event (start/stop), cwd, ts.

### Step 3: Extract Tool Calls per Agent

Grep for `"type": "tool_call"` entries. Group by agent_id. For the main agent (agent_id is null), group separately.

### Step 4: Reconstruct Delegation Tree

Pair delegation start/stop events by agent_id. Establish parent-child nesting by timestamp ordering (a start between another agent's start and stop is a child). Compute max depth.

Steps 2-3 are parallelizable.

## Phase 2 — Trust Checks

Step 5 requires output from Steps 2-4.

### Step 5: Trace-Only Checks (TC-1 through TC-5)

For each check in the reference:
- **TC-1 Orphan:** delegation starts without matching stops
- **TC-2 CWD escape:** tool_call.cwd not under delegation.cwd path prefix
- **TC-3 Depth:** max depth exceeds threshold (default 3)
- **TC-4 Re-delegation:** stop→start same type with no tool_calls between
- **TC-5 Tool escalation:** classify child's tools via L1-L5 model; flag if child uses L4/L5 tools parent never used

### Step 6: Config-Enriched Checks (optional, TC-6/TC-7)

For each delegation with a cwd, attempt: Glob for CLAUDE.md at that path. If found, Grep for `allowed-tools:` in agent configs.

- **TC-6 Scope violation:** agent used tools not in declared allowed-tools
- **TC-7 Undeclared agent:** no agent config matches agent_type at CWD

If CLAUDE.md not found: note "config unavailable for [agent_id] at [cwd]" per agent. Do not fail the check — degrade gracefully.

**Resource caps:** Read ≤100 lines directly, Grep for bulk. ≤5 CLAUDE.md reads for enrichment.

**Error handling:** Grep returns 0 delegation events → "single-agent session, no trust chain to audit" → stop. Grep fails → abort with error.

## Phase 3 — Output

### Status
[contained | advisory | breach]
- `contained` — 0 violations
- `advisory` — only TC-3/TC-4 (Low/Medium, structural concerns)
- `breach` — any TC-1/TC-5/TC-6 (High, trust boundary violation)

### Delegation Tree

```
main
├── agent-A (Plan, cwd=/path) [depth 1]
│   └── agent-B (Explore, cwd=/path) [depth 2]
└── agent-C (Explore, cwd=/path) [depth 1]
```

### Trust Chain Summary

| Metric | Value |
|---|---|
| Agents observed | [N] |
| Max delegation depth | [N] |
| Orphan agents (TC-1) | [N] |
| CWD escapes (TC-2) | [N] |
| Depth violations (TC-3) | [N] |
| Tool escalations (TC-5) | [N] |
| Scope violations (TC-6) | [N] (or "N/A — no config") |

### Trust Violations

[For each violation:]
- **TC-N: [Check name]** (Severity: [H/M/L]) — Agent: [agent_id] ([agent_type]). Evidence: [detail].

[If none: "All delegation chains contained."]

### Recommendations

[1-3 recommendations based on findings.]

## Quality measurement (mandatory before Phase 4 — Report Persistence)

Without verification, this skill fails at **F1 — Predicate incompleteness** (the closed TC-1..TC-7 catalog misses a defect class; the canonical example is a hand-off via `SendMessage` that emits no `SubagentStart` event and escapes all six trace-only checks) and at **F9 — Evidence fabrication** (a violation cites an `agent_id` or timestamp that does not appear in the trace, breaking the "evidence over inference" contract). Trust-chain checks are predicate-class (yes/no per TC rule), so D6 trivially passes; D2 (every violation grounded in trace evidence) and D5 (catalog completeness against `SubagentStart`/`SubagentStop` events) are load-bearing.

Run the three layers BEFORE Phase 4 Step 2 (present report and persist). Treat the unsigned report drafted in Phase 3 as `$REPORT`; treat the analyzed trace JSONL as `$TARGET`. Sensitive-content sweeps (hardcoded user-home prefixes, RFC1918 IPs) are NOT in Layer A — those are enforced at Write time by the `block-sensitive-content.sh` PreToolUse hook, which is the canonical defense; duplicating the regex here would itself violate the doc-content constraint.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024), Beyond Consensus (NUS 2025), `references/trust-chain-model.md` (canonical TC-1..TC-7 catalog with documented severities), `skills/review-claude-config/references/signal-catalog.md` (catalog-completeness reasoning for D5).

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

STATUS_VOCAB = {"contained", "advisory", "breach"}
status_m = re.search(r"^###?\s+Status\s*\n+\[?([\w\-| ]+?)\]?\s*$",
                     body, re.M)
status_pick = None
if status_m:
    raw = status_m.group(1).strip()
    # accept either single token or "a | b | c" template — pick chosen-status
    # on the following non-empty body line
    nxt = re.search(r"^###?\s+Status\s*\n+[\w\-| \[\]]+\n+([\w\-]+)",
                    body, re.M)
    status_pick = nxt.group(1) if nxt else (raw if raw in STATUS_VOCAB else None)

# rule-ids (TC-1..TC-7 closed catalog)
rule_ids = re.findall(r"\bTC-(\d)\b", t)
out_of_catalog = [r for r in rule_ids if int(r) < 1 or int(r) > 7]

# severities
severities = re.findall(r"Severity:\s*([HML])\b", t)
sev_ok = all(s in {"H", "M", "L"} for s in severities)

# documented severity per TC rule (references/trust-chain-model.md)
DOC_SEVERITY = {"1": "H", "2": "M", "3": "M", "4": "L",
                "5": "M", "6": "H", "7": "M"}
sev_per_rule = {}
for m in re.finditer(r"\bTC-(\d)\b[^\n]*?Severity:\s*([HML])", t):
    sev_per_rule.setdefault(m.group(1), set()).add(m.group(2))
inconsistent = {f"TC-{k}": sorted(v)
                for k, v in sev_per_rule.items() if len(v) > 1}
miscalibrated = {f"TC-{k}": (sorted(v), DOC_SEVERITY.get(k))
                 for k, v in sev_per_rule.items()
                 if k in DOC_SEVERITY and (sorted(v) != [DOC_SEVERITY[k]])}

# delegation-depth consistency: max_depth in summary table vs deepest
# indent in ASCII tree (rough heuristic: count leading `│   ` or `    `
# blocks before the first non-space content)
depth_summary_m = re.search(
    r"Max delegation depth\s*\|\s*(\d+)", body)
depth_summary = int(depth_summary_m.group(1)) if depth_summary_m else None
tree_block_m = re.search(r"```\n(main\n(?:[│├└─\s\w\-\(\),=/.\[\]]*\n)*?)```",
                         body)
deepest_indent = None
if tree_block_m:
    indents = []
    for line in tree_block_m.group(1).splitlines():
        if not line.strip() or line.strip() == "main": continue
        # depth = count of "│   " or "    " prefixes before the branch glyph
        m = re.match(r"^((?:[│ ]   )*)[├└]", line)
        if m:
            indents.append(len(m.group(1)) // 4 + 1)
    if indents:
        deepest_indent = max(indents)

# evidence: agent_id references resolvable in trace JSONL
violation_block = re.search(
    r"^### Trust Violations\s*\n(.*?)(?=^###?\s+\w|\Z)", body, re.M | re.S)
agent_ids = []
if violation_block:
    agent_ids = re.findall(r"Agent:\s*([A-Za-z0-9_\-]+)",
                           violation_block.group(1))
missing_agent_ids = []
if target_path and os.path.exists(target_path) and agent_ids:
    with open(target_path) as tf:
        trace = tf.read()
    missing_agent_ids = [aid for aid in agent_ids[:5] if aid not in trace]

# delegation tree presence
tree_present = bool(tree_block_m)

# determinism (SOFT): if env var set, diff TC-rule-id set
det_path = os.environ.get("DETERMINISM_RUN_2_REPORT")
det_diff = None
if det_path and os.path.exists(det_path):
    with open(det_path) as f2: t2 = f2.read()
    rids1 = set(re.findall(r"\bTC-\d\b", t))
    rids2 = set(re.findall(r"\bTC-\d\b", t2))
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
    note="status must be contained|advisory|breach")
add("STRICT", "tc_ids_in_catalog",         f"out_of_range={out_of_catalog}",
    len(out_of_catalog) == 0,
    note="TC-N must be 1..7 per references/trust-chain-model.md")
add("STRICT", "severity_tokens_valid",     f"set={sorted(set(severities))}",
    sev_ok)
add("STRICT", "rule_severity_stable",      f"inconsistent={inconsistent}",
    len(inconsistent) == 0,
    note="one TC rule must carry one severity across the report")
add("STRICT", "rule_severity_calibrated",  f"miscalibrated={miscalibrated}",
    len(miscalibrated) == 0,
    note="severity must match references/trust-chain-model.md")
add("STRICT", "delegation_tree_present",   str(tree_present), tree_present,
    note="ASCII Delegation Tree block must render")
add("STRICT", "delegation_depth_consistent",
    f"summary={depth_summary} tree={deepest_indent}",
    depth_summary is None or deepest_indent is None
    or depth_summary == deepest_indent,
    note="Max delegation depth in summary must equal deepest indent in tree")
if target_path and os.path.exists(target_path):
    add("STRICT", "evidence_agent_ids_present",
        f"missing={missing_agent_ids}",
        len(missing_agent_ids) == 0,
        note="every cited agent_id must appear in the trace JSONL")
if det_diff is not None:
    add("SOFT", "determinism_rule_set",
        f"symmetric_diff={det_diff}", len(det_diff) == 0,
        note="LLM-judged checks may shift the TC-rule set across runs")

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
| `tc_ids_in_catalog`               | F4, F5 (taxonomy drift)|
| `severity_tokens_valid`           | F5, F8                 |
| `rule_severity_stable`            | F8                     |
| `rule_severity_calibrated`        | F8 (vs documented map) |
| `delegation_tree_present`         | F5 (structural break)  |
| `delegation_depth_consistent`     | F8/F9 (count drift)    |
| `evidence_agent_ids_present`      | F9 (fabrication)       |
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

Dispatch a fresh subagent. The critic operates on the pair `(trace JSONL, audit report)`. The TC-1..TC-7 catalog is closed (per `references/trust-chain-model.md`); the critic's job is to find rule firings the audit MISSED or that it ADDED without justification, with explicit attention to the `SendMessage`-without-`SubagentStart` escape vector that defeats all trace-only checks.

```
Agent({
  description: "Blind audit-trust-chain critic (TC-1..TC-7 recall)",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind audit-critic. You are given two artifacts:\n" +
    "\n" +
    "A: a Claude Code audit trace (JSONL with delegation, tool_call, " +
    "and SubagentStart/SubagentStop events).\n" +
    "B: an audit report containing a Delegation Tree (ASCII), a Trust " +
    "Chain Summary table, and a Trust Violations list with rule-ids " +
    "TC-1 (orphan), TC-2 (CWD escape), TC-3 (depth), TC-4 " +
    "(re-delegation), TC-5 (tool escalation), TC-6 (scope violation, " +
    "config-enriched), TC-7 (undeclared agent, config-enriched).\n" +
    "\n" +
    "Documented severities (from references/trust-chain-model.md): " +
    "TC-1=H, TC-2=M, TC-3=M, TC-4=L, TC-5=M, TC-6=H, TC-7=M.\n" +
    "\n" +
    "1. For each finding in B, locate the corresponding evidence in A " +
    "and classify:\n" +
    "   GROUNDED — evidence in A matches the TC rule-id AND the " +
    "asserted severity is the documented one.\n" +
    "   WEAKENED — evidence in A is weaker than the rule-id suggests " +
    "(e.g., severity asserted as H but evidence supports M; or TC-3 " +
    "depth flagged at depth=2).\n" +
    "   ADDED — no evidence in A supports the finding (e.g., cited " +
    "agent_id absent from trace, fabricated CWD escape).\n" +
    "\n" +
    "2. Scan A for signal patterns the report did NOT flag. The " +
    "catalog covers: TC-1 (delegation start with no matching stop), " +
    "TC-2 (tool_call.cwd outside delegation.cwd subtree), TC-3 " +
    "(depth >3), TC-4 (stop→start same agent_type with no tool_calls " +
    "between), TC-5 (child uses L4/L5 tools parent never used), TC-6 " +
    "(agent used tool not in declared allowed-tools), TC-7 (no agent " +
    "config matches agent_type at CWD). If you find a passage in A " +
    "that an alert reader would expect to trigger one of these but no " +
    "finding cites it, classify as:\n" +
    "   DROPPED — rule that should have fired but did not.\n" +
    "\n" +
    "3. Watch specifically for the canonical edge case: a `SendMessage`" +
    " hand-off with no `SubagentStart` event — the resulting delegation " +
    "is invisible to all trace-only checks. If present in A but not " +
    "surfaced anywhere in B, mark it DROPPED with rule-id=`no-rule` " +
    "and reason='catalog-gap'.\n" +
    "\n" +
    "Report ONE block per item. Format:\n" +
    "  [GROUNDED|WEAKENED|ADDED|DROPPED]: TC-N (or 'no-rule' for " +
    "catalog-gap DROPPED)\n" +
    "  evidence_in_A: '<short quote or jsonl line ref>'\n" +
    "  evidence_in_B: '<short quote or finding-id>'\n" +
    "  reason: <≤2 sentences>\n" +
    "\n" +
    "Do not rate report quality. Do not summarize. Report under 500 " +
    "words.\n" +
    "\n" +
    "A:\n<paste $TARGET; for traces >5KB paste first 2KB + sampled " +
    "middle/end blocks plus all SubagentStart/Stop events>\n" +
    "\n" +
    "B:\n<paste $REPORT contents>"
})
```

**Order-swap mandate**: dispatch a second time with artifact labels reversed (A=report, B=trace JSONL). Take the union of items flagged across both runs (de-dup by `rule-id × evidence_in_A`). Position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791).

Output vocabulary maps to Layer C as: `GROUNDED` → no impact; `ADDED` → D2 NO; `WEAKENED` → D4 NO; `DROPPED` (TC-1..TC-7) → D5 NO; `DROPPED` (`no-rule` / catalog-gap) → D5 NO with explicit meta-finding ("catalog needs extension").

### Layer C — binary rubric (6 yes/no dimensions)

```
D1 STATUS_VOCAB_CONFORMANT    The `### Status` line and the
                              `summary[].status` frontmatter field both
                              hold a value in the closed set
                              {contained, advisory, breach}. Frontmatter
                              schema_version is the pinned value. Catches
                              F5, F10.

D2 EVIDENCE_GROUNDED          Every TC-N violation cites a concrete
                              `agent_id` AND timestamps AND a `cwd` (for
                              TC-2/TC-6) AND a tool name (for TC-5/TC-6),
                              all resolvable in $TARGET (Layer A
                              agent_id-presence check passed AND no
                              Layer-B ADDED items). Catches F2, F9.

D3 TAXONOMY_DISJOINT          No two findings cite distinct TC rule-ids
                              for the same evidence span (same
                              agent_id × event window). Every cited rule
                              is in the documented closed set
                              {TC-1..TC-7}. Catches F4.

D4 SEVERITY_CALIBRATED        Each TC rule appears with a single
                              severity across the report; that severity
                              matches the documented map (TC-1=H, TC-2=M,
                              TC-3=M, TC-4=L, TC-5=M, TC-6=H, TC-7=M per
                              references/trust-chain-model.md). No
                              Layer-B WEAKENED items survive. Catches
                              F8.

D5 RULE_CATALOG_COMPLETENESS  Layer-B critic surfaced ZERO `DROPPED`
                              items. Every documented TC-N that the trace
                              evidence supports must appear in the
                              report at least once; conversely, any
                              passage that an alert reader would expect
                              to trigger TC-1..TC-7 has a corresponding
                              violation. `no-rule` / catalog-gap DROPPED
                              items (e.g. SendMessage-without-
                              SubagentStart) surface a meta-finding;
                              the catalog itself needs extension and
                              the report MUST flag the gap explicitly.
                              Catches F1, F3.

D6 DISCOVERY_PRECISION        Trivially YES — `audit-trust-chain` emits
                              predicate-class violations only (TC-1..
                              TC-7); no heuristic discovery surface.
                              Catches F7 (vacuously).
```

Layer-A row → Dimension mapping:
- `frontmatter_present`, `required_frontmatter_keys`, `schema_version_pinned`, `status_in_vocab` → D1
- `evidence_agent_ids_present`, `delegation_tree_present`, `delegation_depth_consistent` → D2
- `tc_ids_in_catalog` → D3
- `severity_tokens_valid`, `rule_severity_stable`, `rule_severity_calibrated` → D4

Layer-B item → Dimension mapping:
- `ADDED` → D2 NO
- `WEAKENED` → D4 NO
- `DROPPED` (TC-1..TC-7) → D5 NO
- `DROPPED` (`no-rule` / catalog-gap) → D5 NO + meta-finding footnote
- `GROUNDED` → no impact

### Reconciliation outcomes

- **All STRICT pass + zero ADDED/WEAKENED/DROPPED** → proceed to Phase 4 (Report Persistence).
- **Any STRICT fail OR any ADDED/WEAKENED/DROPPED** → patch inline: drop fabricated violations, recalibrate severities against the documented map, add dropped rule firings. Re-run Layer A on the patched report. Max 2 iterations. If still failing after iteration 2, surface to user with the full ledger and DO NOT persist the report to `${HOME}/.claude/plugins/data/claude-config/reports/`.
- **Only SOFT warnings** (e.g., `determinism_rule_set` symmetric-diff non-empty) → append a footnote ("This audit was non-deterministic across runs; TC-rule set may vary") and proceed.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **SendMessage-without-SubagentStart catalog gap** — the canonical F1 case for this skill. A hand-off via `SendMessage` that emits no `SubagentStart` event escapes all of TC-1..TC-7 because every trace-only check is keyed on those events. Layer B surfaces it as `no-rule` DROPPED, but resolving it requires extending the catalog (adding a TC-8 for hand-off-without-start) — the pipeline cannot patch the rule catalog in-session. Mitigation: report the meta-finding as a recommendation in the Recommendations section.
2. **Cross-trace correlation gaps** — the pipeline judges one report against its single trace. A pattern visible only across multiple sessions (e.g., a slowly-escalating tool-grant pattern detectable only when 10 traces are co-analyzed) escapes both Layers A and B. Mitigation: cross-trace analysis is `/review-analytics`'s remit, not this skill's.
3. **CLAUDE.md staleness for TC-6/TC-7** — config-enriched checks read the on-disk `allowed-tools:` declaration at audit time, which may differ from the declaration that was active when the delegation ran. The pipeline cannot reconstruct historical config state; the report MUST note when TC-6/TC-7 evidence relies on the current CLAUDE.md.
4. **L1–L5 tool-classification heuristic** — TC-5 tool-escalation depends on an action-classification model (L1 read-only … L5 destructive) that is itself a repo-policy heuristic. Layer A checks severity calibration against the documented map; it does not validate the L1–L5 mapping itself against an external ground truth.

The Output report MUST list which residual classes apply when the critic surfaces `no-rule` DROPPED items or when SOFT determinism warnings fire, so the user has one last human-glance opportunity.

## Phase 4 — Report Persistence

1. Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)
2. Present report. Confirm before writing to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-audit-trust-chain.md`.
3. Frontmatter:
   ```yaml
   ---
   generated_by: audit-trust-chain
   schema_version: 1
   date: YYYY-MM-DD
   repo: <slug>
   origin: <git-remote-url>    # Optional
   target: /path/to/trace.jsonl
   summary:
     - name: trust-chain
       type: TrustChain
       path: relative/path/to/trace.jsonl
       status: contained|advisory|breach
       agents: N
       max_depth: N
       violations: N
   ---
   ```

## Hard Rules

- **Read-only on the trace.** Write only to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Tier A justification:** Write for report persistence. Grep/Read for trace + optional CLAUDE.md parsing.
- **Graceful degradation.** Missing CLAUDE.md = skip config-enriched checks, not abort.
- **Evidence over inference.** Every violation cites agent_id, timestamps, and concrete data.
- **Present the full report before any follow-up actions.**

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
