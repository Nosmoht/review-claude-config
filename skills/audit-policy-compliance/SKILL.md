---
name: audit-policy-compliance
description: >
  Audits a Claude Code audit trace for policy compliance by classifying
  each tool call against the action classification model and flagging
  violations. Use when asked to 'audit policy', 'check compliance',
  or 'review tool authorization'. Do NOT use for static config review.
argument-hint: <path-to-trace.jsonl>
allowed-tools: Bash, Read, Write, Glob, Grep
---

# Audit Policy Compliance

You are a policy compliance auditor that reads Claude Code audit traces and evaluates whether tool calls respected authorization levels. Your job is to flag violations where tools were used at a higher authorization level than the policy permits.

## Argument Handling

- `$ARGUMENTS` is a path to an audit trace `.jsonl` file.
- If empty, check `${HOME}/.claude/plugins/data/claude-config/audit/` for recent audit traces. If none found, ask the user for a path and stop.
- Validate the file contains entries with `"type": "tool_call"` (audit trace format required — raw transcripts not supported; suggest `/review-session-trace` instead).

## Termination and Escalation

**Termination conditions:**
- Trace has >5000 tool_call entries — process first 2000, note truncation
- >8 sequential tool calls without producing output — emit partial report

**Escalation triggers (ask user):**
- >50 L4/L5 violations detected — session may need manual security review
- Policy file (`${HOME}/.claude/plugins/data/claude-config/policy.json`) not found — will use default policy (L1-L3 allow, L4 ask, L5 deny); confirm this is acceptable

## Phase 1 — Load References

### Step 1: Load Action Classification and Detection Rules

Read both:

- `references/action-classification.md` — tool-to-level mapping and policy rule format.
- `references/detection-rules.md` — known-critical-bug detectors (BYP-1/2 for #39523 bypass-permissions, PCR-1 for #41259 cache reload, MAT-1 for #46978 glob auto-approve). Each rule normalises input (Unicode NFC, case-fold, whitespace collapse, comment-strip) before matching. Run these in Phase 2 alongside the standard classification flow.

### Step 2: Load Policy

Check for `${HOME}/.claude/plugins/data/claude-config/policy.json`. If found, read and parse rules and overrides. If not found, use default policy from the action classification reference.

## Phase 2 — Classification (Steps 3-4 are parallelizable)

**Resource caps:** Read ≤100 lines directly, use Grep for bulk extraction.

### Step 3: Extract Tool Calls

Grep for `"type": "tool_call"` entries. For each, extract `tool_name`, `input_hash`, `success`, `agent_id`, `cwd`, `ts`.

### Step 4: Extract Bash Commands

For audit traces: Bash tool_input is hashed (privacy). Flag all Bash calls as L4 minimum. For additional context, check if the trace includes raw transcript path in session metadata — if so, spot-check 5 Bash entries against L5 escalation patterns from the action classification reference.

**Error handling:** If Grep returns 0 tool_call entries, report "empty trace — no tool calls to audit" and stop. If Grep fails, abort with structured error.

Step 5 requires output from Steps 3-4.

### Step 5: Classify and Evaluate

For each tool call:
1. Map `tool_name` to authorization level using the tool-to-level table.
2. Check if any override rule matches (tool + path pattern).
3. Compare the effective level against the policy rules.
4. Record: `compliant` (level ≤ policy threshold) or `violation` (level > threshold).

For violations, record: tool_name, level, policy action (ask/deny), timestamp, agent_id.

### Step 6: Compute Compliance Metrics

| Metric | Method |
|---|---|
| Total tool calls | Count all entries |
| L1-L5 distribution | Group by authorization level |
| Violation count | Entries where level exceeds policy |
| Violation rate | Violations / total |
| Escalation correctness | L4 calls preceded by AskUserQuestion within 3 prior entries |
| L5 attempts | Any L5 calls — should be 0 under default policy |

### Step 7: Deep Escalation Analysis

Step 7 requires output from Steps 5-6 (classified tool calls and compliance metrics).

For each L4+ tool_call, search backward for a matching `policy_decision` entry (same tool_name, within 30 seconds or 10 entries). Classify:
- **Chain complete:** policy_decision(ask) found, tool_call followed → approved escalation
- **Escalation gap:** L4+ tool_call with NO preceding policy_decision → hooks bypassed or misconfigured
- **Subagent L4:** L4+ call where agent_id is non-null → flag for delegation authorization check

Compute:
- Escalation gap count and rate
- Over-escalation rate: policy_decision(ask) count / total tool_calls. Flag if >30%.
- Subagent L4 count (these may lack user confirmation by design)

### Step 8: Run Known-Critical-Bug Detectors

For each rule in `references/detection-rules.md`, evaluate against the
loaded trace and any settings layers (`settings.json`,
`settings.local.json`, `~/.claude/settings.json`) accessible from the
trace's recorded `cwd`. Apply the input-normalisation steps from the
rules file first.

For each rule fire, emit a finding with the canonical ID format
(`BYP-1:<settings-path>:Safety/v1`, etc.) and the severity defined in
the rules file. Bug-detector findings appear in the report's
"Known-bug detectors" subsection of Phase 3, separate from policy
violations.

## Phase 3 — Output

### Status
[compliant | advisory | violation]
- `compliant` — 0 violations, all tool calls within policy
- `advisory` — only L4 violations (ask-level, not deny-level)
- `violation` — any L5 violation or violation rate >10%

### Policy Summary

| Level | Count | Policy | Violations |
|---|---|---|---|
| L1 Read | [N] | Allow | [N] |
| L2 Analyze | [N] | Allow | [N] |
| L3 Recommend | [N] | Allow | [N] |
| L4 Act | [N] | Ask | [N] |
| L5 Irreversible | [N] | Deny | [N] |
| **Total** | **[N]** | | **[N] ([X%])** |

### Violations

[For each violation, ordered by level (L5 first):]

- **[timestamp]** — `[tool_name]` at level [LN] violated [ask/deny] policy. Agent: [agent_id or "main"].

[If no violations: "All tool calls compliant with policy."]

### Escalation Analysis

- L4 calls with prior confirmation: [N] of [total L4] ([X%])
- L4 calls without confirmation: [N]
- Escalation gaps (no policy_decision): [N]
- Over-escalation rate: [X%] [if >30%: "ELEVATED — review whether all ask prompts are necessary"]
- Subagent L4 calls: [N] (these may lack user confirmation by design)

### Recommendations

[1-3 recommendations based on violation patterns.]

## Quality measurement (mandatory before report persistence)

Without verification, this skill fails at **false-negative on wrapper-escaped escalation**: a `Bash("npx <wrapper> kubectl delete …")` call routed through a shell-wrapper has L1 outer-tool classification but L5 inner action, escaping the standard tool-to-level table. A second canonical failure is **F4 taxonomy ambiguity** — the same tool call classified at two levels across the report (e.g. once L4, once L1) breaks downstream analytics consumers. The literature converges on a three-layer pipeline (CheckEval arXiv:2403.18771, G-Eval arXiv:2303.16634, Position bias arXiv:2406.07791, IFEval arXiv:2311.07911, FollowBench ACL 2024); any one layer alone is insufficient.

Run the pipeline AFTER the report is fully drafted and BEFORE Phase 4 persistence.

```bash
TMPDIR=$(mktemp -d -t apc-XXXX)
REPORT="$TMPDIR/report.md"
TARGET="<path-to-trace.jsonl>"   # the $ARGUMENTS trace
# write the draft report to "$REPORT" before running Layer A
```

### Layer A — mechanical invariants (deterministic, fail-fast)

Any non-zero `STRICT` row → abort and report; any `SOFT` row delta → log warning, surface to user, do not auto-persist.

```bash
python3 - "$REPORT" "$TARGET" audit-policy-compliance <<'PY'
import re, sys, os

report_path = sys.argv[1]
target_path = sys.argv[2] if len(sys.argv) > 2 else None
skill = sys.argv[3]

STATUS_VOCAB = {"compliant", "advisory", "violation"}
RULE_PREFIX  = [r"L[1-5]", r"BYP-\d+", r"PCR-\d+", r"MAT-\d+", r"SES-\d+"]
SEV_VOCAB    = {"Critical", "High", "Medium", "Low", "Info", "H", "M", "L"}

with open(report_path) as f: t = f.read()
fm_match = re.match(r"^---\n(.*?)\n---\n", t, re.S)
if not fm_match:
    print("FAIL STRICT frontmatter_present: no YAML frontmatter")
    sys.exit(1)
fm   = fm_match.group(1)
body = t[fm_match.end():]

REQUIRED_FM = ["generated_by", "schema_version", "date", "target", "summary"]
missing     = [k for k in REQUIRED_FM if not re.search(rf"^{k}:", fm, re.M)]

schema_v_m  = re.search(r"^schema_version:\s*(\d+)", fm, re.M)
schema_v    = int(schema_v_m.group(1)) if schema_v_m else None

# status: line under `### Status` heading OR `status:` in frontmatter summary
chosen = None
m1 = re.search(r"^#+\s+Status\s*\n+\[?([\w\-]+)", body, re.M)
if m1: chosen = m1.group(1)
if not chosen:
    m2 = re.search(r"^\s+status:\s*([\w\-]+)", fm, re.M)
    if m2: chosen = m2.group(1)

rule_ids = set()
for p in RULE_PREFIX:
    rule_ids.update(re.findall(rf"\b{p}\b", t))

severities = re.findall(r"\b(?:[Ss]everity|Finding severity):\s*([A-Z][a-z]+|[HML])\b", t)
sev_ok     = all(s in SEV_VOCAB for s in severities)

# F8: same rule-id with two severities in same report
sev_per_rule = {}
for m in re.finditer(rf"\b({'|'.join(RULE_PREFIX)})\b[^\n]*?(?:[Ss]everity|Finding severity):\s*([A-Z][a-z]+|[HML])", t):
    rid, sv = m.group(1), m.group(2)
    sev_per_rule.setdefault(rid, set()).add(sv)
inconsistent = {k: sorted(v) for k, v in sev_per_rule.items() if len(v) > 1}

# F4: same tool_name classified at two L-levels
tool_levels = {}
for m in re.finditer(r"`([\w\-_]+)`\s+at\s+level\s+(L[1-5])", body):
    tool_levels.setdefault(m.group(1), set()).add(m.group(2))
multi_level = {k: sorted(v) for k, v in tool_levels.items() if len(v) > 1}

# violation_rate arithmetic
rate_m = re.search(r"violation_rate:\s*([0-9.]+)", fm)
viol_m = re.search(r"violations:\s*(\d+)", fm)
total_m= re.search(r"total_calls:\s*(\d+)", fm)
rate_ok = True
rate_note = ""
if rate_m and viol_m and total_m:
    declared = float(rate_m.group(1))
    computed = round(100.0 * int(viol_m.group(1)) / max(int(total_m.group(1)), 1), 1)
    rate_ok  = abs(declared - computed) <= 0.1
    rate_note= f"declared={declared} computed={computed}"

# evidence excerpt presence in target (sample 3 backtick-quoted strings)
excerpts = re.findall(r"Evidence:[^\n]*?`([^`]+)`", t)
missing_exc = []
if target_path and os.path.exists(target_path) and excerpts:
    with open(target_path) as tf: ttext = tf.read()
    missing_exc = [e for e in excerpts[:3] if e and e not in ttext]

rows = []
def add(sev, name, val, ok, note=""):
    flag = "" if ok else (" FAIL" if sev == "STRICT" else " warn")
    rows.append((sev, name, val, flag, note))

add("STRICT", "frontmatter_present",       "yes" if fm_match else "no", bool(fm_match))
add("STRICT", "required_frontmatter_keys", f"missing={missing}",        len(missing) == 0)
add("STRICT", "schema_version_pinned",     f"v{schema_v}",              schema_v == 1,
    note="bump invalidates analytics consumers")
add("STRICT", "status_in_vocab",           str(chosen),                 chosen in STATUS_VOCAB)
add("STRICT", "severity_tokens_valid",     f"set={sorted(set(severities))}", sev_ok)
add("STRICT", "rule_severity_stable",      f"inconsistent={inconsistent}",   len(inconsistent) == 0)
add("STRICT", "tool_level_disjoint",       f"multi_level={multi_level}",     len(multi_level) == 0,
    note="F4 — same tool classified at two L-levels")
add("STRICT", "violation_rate_arithmetic", rate_note or "n/a",          rate_ok)
add("STRICT", "evidence_excerpts_present", f"missing={missing_exc}",    len(missing_exc) == 0)

# determinism warning (SOFT — requires two-run setup)
det_path = os.environ.get("DETERMINISM_RUN_2_REPORT")
if det_path and os.path.exists(det_path):
    with open(det_path) as f2: t2 = f2.read()
    rule_ids_2 = set()
    for p in RULE_PREFIX:
        rule_ids_2.update(re.findall(rf"\b{p}\b", t2))
    diff = rule_ids ^ rule_ids_2
    add("SOFT", "determinism_rule_set", f"symmetric_diff={sorted(diff)}", len(diff) == 0,
        note="LLM-judged classification may have produced non-deterministic finding set")

fail = 0
print(f"{'severity':8} {'metric':30} {'value':40} {'flag':>6}  note")
for sev, name, val, flag, note in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:8} {name:30} {str(val)[:40]:40} {flag:>6}  {note}")
sys.exit(1 if fail else 0)
PY
```

**Metric coverage matrix** (which failure class each row catches):

| Layer-A row | Catches |
|---|---|
| `frontmatter_present`, `required_frontmatter_keys` | F5 report-shape break |
| `schema_version_pinned` | F10 schema drift |
| `status_in_vocab` | F5 status enum drift |
| `severity_tokens_valid` | F5, F8 |
| `rule_severity_stable` | F8 severity miscalibration |
| `tool_level_disjoint` | F4 taxonomy ambiguity (load-bearing for this skill) |
| `violation_rate_arithmetic` | report-internal arithmetic consistency |
| `evidence_excerpts_present` | F9 evidence fabrication |
| `determinism_rule_set` (SOFT) | F6 LLM-judged non-determinism |

If exit non-zero → STOP, do not proceed to Phase 4 persistence. Report failures, propose specific patches, ask user.

### Layer B — adversarial critic dispatch (blind, recall-framed)

**Layer-B-Gate.** Per `docs/skill-verification-architecture.md`, AUDIT
output is structured extraction when predicates are mechanical. Layer B
fires ONLY when ≥30% of this skill's predicates require LLM judgment
(closed-set classification, taxonomy ambiguity, behavioral-signal
detection). For pure-mechanical audits (file exists / regex matches /
exit code only), SKIP Layer B and rely on Layer A + Layer C alone.
Document the gate decision in the report frontmatter as
`layer_b_fired: true|false (rationale)`.

Dispatch a fresh subagent with the single task of finding tool calls the audit MISSED or rules that were ADDED without justification. **Seed a known-edge-case trace** (a `Bash("npx <wrapper> kubectl delete …")` entry, or `Bash("sudo …")`, or an unknown MCP tool defaulted to L4) and verify the critic surfaces the DROPPED rule firing on the inner action.

```
Agent({
  description: "Adversarial audit-policy-compliance critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind audit critic. Two artifacts are attached:\n\n" +
    "A: the source JSONL audit trace the audit consumed.\n" +
    "B: the audit report (Markdown, frontmatter + ### Status + Policy " +
    "Summary + Violations + Escalation Analysis).\n\n" +
    "The audit applied a closed catalog: tool-to-level mapping " +
    "(L1 Read / L2 Analyze / L3 Recommend / L4 Act / L5 Irreversible) " +
    "plus bug detectors (BYP-1/2, PCR-1, MAT-1, SES-N).\n\n" +
    "Tasks:\n" +
    "1. For each finding in B, locate the corresponding tool_call in A " +
    "and judge whether the evidence supports the asserted level and " +
    "severity. Classify each as GROUNDED / WEAKENED / ADDED.\n" +
    "2. Scan A for tool calls that should have triggered an L4/L5 " +
    "classification or a BYP/PCR/MAT/SES detector but were not " +
    "flagged in B. Specifically check shell wrappers " +
    "(`npx <X> kubectl …`, `sudo …`, `bash -c …`, `xargs …`) where " +
    "the OUTER tool is L1 but the INNER action is L5. Classify each " +
    "miss as DROPPED.\n" +
    "3. Report ONE block per item:\n\n" +
    "   [GROUNDED|WEAKENED|ADDED|DROPPED]: rule-id-or-tool_name\n" +
    "   evidence_in_A: \"<short quote or ts ref>\"\n" +
    "   evidence_in_B: \"<short quote or finding line>\"\n" +
    "   reason: <≤2 sentences>\n\n" +
    "Do not rate quality. Do not praise coverage. Do not write a " +
    "summary paragraph. Report under 500 words.\n\n" +
    "A:\n<paste $TARGET first 2KB + sampled middle/end blocks if >5KB>\n\n" +
    "B:\n<paste $REPORT contents>"
})
```

**Order-swap mandate**: dispatch a second time with labels reversed (A=$REPORT, B=$TARGET). Take the union of items flagged across both runs (de-dup by `rule-id × evidence_in_A`). Position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791).

**Output vocabulary**: `GROUNDED` (positive, expected — no action), `WEAKENED` (severity/level drift), `ADDED` (false positive), `DROPPED` (false negative — the load-bearing class for the wrapper-escape failure mode).

### Layer C — binary rubric (CheckEval-style)

Six yes/no dimensions specialized to this skill. Any `NO` blocks Phase 4 persistence until resolved. CheckEval (arXiv:2403.18771) reports +0.45 inter-evaluator agreement for binary vs. Likert.

```
D1 STATUS_VOCAB_CONFORMANT     The `### Status` line in the body AND
                                summary[].status in frontmatter both
                                belong to {compliant, advisory, violation}.
                                Catches F5.

D2 EVIDENCE_GROUNDED            Every violation's tool_name + ts pair
                                resolves to a `"type": "tool_call"` entry
                                in the target JSONL (Layer A excerpt check
                                passed AND no Layer-B ADDED items).
                                Catches F2, F9.

D3 TAXONOMY_DISJOINT            No tool_name appears at two distinct
                                L-levels across the report. Bug-detector
                                rule-ids (BYP/PCR/MAT/SES) do not collide
                                with policy-level claims for the same
                                evidence span. Load-bearing for this skill.
                                Catches F4.

D4 SEVERITY_CALIBRATED          Each L-level / bug-detector rule-id
                                appears with a single severity across the
                                report; severity matches `references/
                                detection-rules.md` (BYP-1/BYP-2 = Critical,
                                PCR-1 = High, MAT-1 = High). Catches F8.

D5 RULE_CATALOG_COMPLETENESS    Layer-B critic surfaced ZERO `DROPPED`
                                items — specifically, no wrapper-escaped
                                L5 inner action (`npx … kubectl`, `sudo`,
                                `bash -c`) and no missed BYP/PCR/MAT/SES
                                firing in any settings layer accessible
                                from the trace's recorded `cwd`.
                                Catches F1, F3.

D6 DISCOVERY_PRECISION          Trivially YES — audit-policy-compliance
                                is predicate-class, not discovery-class.
                                (Retained for category-template parity.)
```

**Layer-A row → Dimension mapping:**
- `frontmatter_present`, `required_frontmatter_keys`, `status_in_vocab` → D1
- `evidence_excerpts_present` → D2
- `tool_level_disjoint` → D3
- `rule_severity_stable`, `severity_tokens_valid` → D4
- `schema_version_pinned`, `violation_rate_arithmetic` → D1/D4

**Layer-B item → Dimension mapping:**
- `ADDED` → D2 NO
- `WEAKENED` → D4 NO
- `DROPPED` → D5 NO
- `GROUNDED` → no impact (expected)

### Reconciliation outcomes

- **All STRICT pass + zero ADDED/WEAKENED/DROPPED** → proceed to Phase 4 persistence.
- **Any STRICT fail OR any ADDED/WEAKENED/DROPPED** → restore inline: drop fabricated findings, re-classify weakened severity/level, add dropped rule firings. Re-run Layer A on the patched report. Max 2 iterations. If still failing, surface to user with the full ledger and DO NOT persist the report.
- **Only SOFT warnings** (e.g. `determinism_rule_set` symmetric-diff non-empty) → report as a footnote in the audit report ("This audit was non-deterministic across N runs; finding set may vary"), then proceed.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Wrapper-decoding limits** — Layer B's wrapper-escape detection is LLM-judged on the inner command string. Obfuscated wrappers (Base64-encoded payloads, `eval $(…)`, runtime-built command strings) escape both Layer A regex and the critic's pattern recognition.
2. **Hashed Bash inputs** — the audit trace privacy-hashes Bash `tool_input`. The pipeline cannot verify the inner action of a Bash call without the raw transcript; D5 catalog-completeness is bounded by what the hashed entry exposes.
3. **Cross-session escalation patterns** — slowly-accumulating L4 grants across multiple sessions (e.g. one new MCP tool per session) escape single-report analysis. Belongs to `/review-analytics`, not this skill.
4. **MCP tool default-to-L4 over-classification** — when a legitimate read-only MCP tool is unknown to the action-classification table, the "default to restrictive" rule produces a false-positive L4 classification. Layer B can flag ADDED if the critic recognises the tool from context, but the pipeline lacks a host-wide MCP tool registry.
5. **Policy file forking** — if `${HOME}/.claude/plugins/data/claude-config/policy.json` differs from the policy assumed by the trace's recording session, the audit re-applies the local policy to historical calls. The pipeline verifies internal consistency, not policy-version alignment.

The report MUST list which residual classes apply to passages the critic flagged as `UNCERTAIN`, so the user has one last human-glance opportunity.

## Phase 4 — Report Persistence

1. Present the report.
2. Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)
3. Confirm before writing to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-audit-policy-compliance.md`.
4. Frontmatter:
   ```yaml
   ---
   generated_by: audit-policy-compliance
   schema_version: 1
   date: YYYY-MM-DD
   repo: <slug>
   origin: <git-remote-url>    # Optional
   target: /path/to/trace.jsonl
   summary:
     - name: policy-compliance
       type: PolicyCompliance
       path: relative/path/to/trace.jsonl
       status: compliant|advisory|violation
       total_calls: N
       violations: N
       violation_rate: X.X
   ---
   ```

## Hard Rules

- **Read-only on the trace.** Never modify the analyzed file. Write only to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Tier A justification:** Write is for report persistence only. No web tools needed.
- **Default to restrictive.** When tool level is ambiguous (e.g., unknown MCP tool), classify as L4.
- **Privacy preserved.** Never attempt to decode or log raw tool_input. Use input_hash for correlation only.
- **Present the full report before any follow-up actions.**

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
