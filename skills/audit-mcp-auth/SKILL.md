---
name: audit-mcp-auth
description: >
  Audits MCP OAuth credential storage for the #45551 race condition that
  can wipe Team-plan workspaces' shared keychain entry. Use when
  asked to 'audit mcp auth', 'check mcp credentials', or after a
  reported team-wide MCP logout. Do NOT use for static .mcp.json review —
  use /review-mcp-server.
argument-hint: "[macOS keychain account name]"
allowed-tools: Read, Bash, Glob, Grep
---

# Audit MCP OAuth Credential Store

You are an MCP credential-store auditor. Your job is to detect the
preconditions of GitHub issue #45551 (MCP OAuth credential-store race
on macOS Team plans, which can corrupt or wipe the shared
`Claude Code-credentials` keychain entry and log out the entire
workspace).

This skill is read-only. It never writes to the keychain, never
re-issues OAuth, never restarts MCP servers. It only inspects.

## Argument Handling

- `$ARGUMENTS` is an optional macOS keychain account name override.
- If empty, default to account `Claude Code-credentials`.
- On non-macOS hosts, report "audit only applicable to macOS hosts" and stop. Do NOT attempt detection on Linux/Windows.

## Termination and Escalation

**Termination conditions:**

- `security find-generic-password` not available (not macOS or stripped binary) — abort with platform notice.
- Keychain entry not found — report "no MCP credential entry; either logged out or never used MCP OAuth" and stop without flagging Critical.

**Escalation triggers:**

- ≥1 detector fires AND user reports active MCP usage by ≥2 teammates — recommend immediate password rotation + manual `claude /mcp reconnect`.
- Keychain JSON parse failure — surface as evidence; do not retry.

## Phase 1 — Discover Preconditions

### Step 1: Confirm macOS

Run `uname -s`. If output is not `Darwin`, abort.

### Step 2: Locate keychain entry

Run, suppressing stderr, capturing the entry:

```bash
security find-generic-password -a "<account>" -s "Claude Code-credentials" -w
```

If the command exits non-zero, treat as "no entry".

### Step 3: Inspect entry size

The bug truncates entries above ~2010 bytes due to a libsecurity buffer
limit. Capture `wc -c` on the entry contents. If size > 2010, raise
KCH-1 (truncation risk).

### Step 4: Check session multiplicity

List active Claude Code processes:

```bash
ps -ax -o pid,command | grep -E "claude( |$)" | grep -v grep
```

Count distinct sessions (one per `claude` process, excluding helper
binaries). If count > 5, raise SES-1 (concurrency above empirically-
observed corruption threshold).

### Step 5: Parse and validate keychain JSON

Pipe the entry contents through a comment-tolerant JSON parser. If
parsing fails OR the parsed object lacks `claudeAiOauth` key, raise
KCH-2 (corruption-likely).

## Phase 2 — Detector Rules

Load `references/detector-rules.md` for the rule details, severity
mappings, and adversarial test cases.

## Phase 3 — Report

Emit a Markdown report with:

- Host platform + macOS version (Bash: `sw_vers -productVersion`).
- Active session count.
- Keychain entry presence + size.
- Per-rule findings (KCH-1, KCH-2, SES-1) with severity.
- Recommendation block: bug URL (#45551), suggested next steps (do NOT
  open a 6th concurrent session; rotate OAuth tokens via `claude
  /logout` then `claude /login` before truncation occurs; back up
  `~/.config/claude/credentials.local` if present).

## Quality measurement (mandatory before Output)

Without verification, this skill fails at **predicate misclassification on system-level state with no ground-truth oracle**. Concrete: a Keychain entry of 2050 bytes from a non-Claude OAuth app could be flagged KCH-1 (truncation risk) even though it has nothing to do with #45551, or a corrupted entry could be missed because the JSON parser tolerated a malformed shape. The skill reads SYSTEM-LEVEL state (`sw_vers`, `security`, `ps`) and there is no oracle for "this entry is legitimate vs corrupted-by-#45551" — only the rule's premise check. The literature (CheckEval arXiv:2403.18771, G-Eval arXiv:2303.16634, Shi et al. 2024 arXiv:2406.07791, FollowBench ACL 2024) converges on a three-layer pipeline; any one layer alone is insufficient. Run all three layers before persisting the report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.

Write the report to a tempdir first so subsequent layers can read it deterministically:

```bash
TMPDIR=$(mktemp -d -t audit-mcp-auth-XXXX)
REPORT="$TMPDIR/report.md"
# write the produced audit report to "$REPORT" before running Layer A
```

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the produced report. Any non-zero `STRICT` row → abort and report; any `SOFT` row delta → log warning, surface to user, do not auto-persist.

```bash
python3 - "$REPORT" <<'PY'
import re, sys, os

with open(sys.argv[1]) as f: t = f.read()

# closed-set status vocab for this skill — keep aligned with audit-template.md
STATUS_VOCAB = {"healthy", "warning", "critical"}
RULE_PREFIXES = [r"KCH-\d+", r"SES-\d+"]

# parse frontmatter
fm_match = re.match(r"^---\n(.*?)\n---\n", t, re.S)
fm = fm_match.group(1) if fm_match else ""
body = t[fm_match.end():] if fm_match else t

REQUIRED_FM = ["generated_by", "schema_version", "date", "target", "summary"]
missing = [k for k in REQUIRED_FM if not re.search(rf"^{k}:", fm, re.M)]

schema_v_match = re.search(r"^schema_version:\s*(\d+)", fm, re.M)
schema_v = int(schema_v_match.group(1)) if schema_v_match else None

# rule-id set
rule_ids = set()
for p in RULE_PREFIXES:
    rule_ids.update(re.findall(rf"\b{p}\b", t))

# severity tokens (per the report's "Severity: H|M|L" form)
severities = re.findall(r"\bSeverity:\s*([HML])\b", t)
sev_ok = all(s in {"H", "M", "L"} for s in severities)

# status pick — body line or "Status:" inline
status_line = re.search(r"^Status:\s*\[?([\w\-]+)", body, re.M)
if not status_line:
    s2 = re.search(r"^#+\s+Status\s*\n+([\w\-]+)", body, re.M)
    chosen = s2.group(1) if s2 else None
else:
    chosen = status_line.group(1)

# skill-specific STRICT rows (per audit-template.md §audit-mcp-auth)
host_platform_ok = bool(re.search(r"\b\d+\.\d+(\.\d+)?\b.*macOS|macOS.*\b\d+\.\d+", body) or re.search(r"productVersion|sw_vers", body, re.I))
# Redaction: no Base64-looking string >256 chars anywhere in body
b64_long = re.findall(r"[A-Za-z0-9+/=]{257,}", body)
redaction_ok = len(b64_long) == 0

# severity-rule consistency
sev_per_rule = {}
for m in re.finditer(rf"\b({'|'.join(RULE_PREFIXES)})\b[^\n]*?Severity:\s*([HML])", t):
    rid, sv = m.group(1), m.group(2)
    sev_per_rule.setdefault(rid, set()).add(sv)
inconsistent = {k: sorted(v) for k, v in sev_per_rule.items() if len(v) > 1}

rows = []
def add(sev, name, val, ok, note=""):
    flag = "" if ok else (" FAIL" if sev == "STRICT" else " warn")
    rows.append((sev, name, val, flag, note))

add("STRICT", "frontmatter_present",       "yes" if fm_match else "no", bool(fm_match))
add("STRICT", "required_frontmatter_keys", f"missing={missing}",        len(missing) == 0)
add("STRICT", "schema_version_pinned",     f"v{schema_v}",              schema_v == 1, note="bump invalidates analytics consumers")
add("STRICT", "severity_tokens_valid",     f"set={sorted(set(severities))}", sev_ok)
if chosen is not None:
    add("STRICT", "status_in_vocab",       chosen,                      chosen in STATUS_VOCAB)
add("STRICT", "rule_severity_stable",      f"inconsistent={inconsistent}", len(inconsistent) == 0)
add("STRICT", "host_platform_present",     "yes" if host_platform_ok else "no", host_platform_ok, note="sw_vers / macOS version must appear in body")
add("STRICT", "keychain_entry_redacted",   f"long_b64_count={len(b64_long)}", redaction_ok, note="no Base64 string >256 chars in body")

# Determinism SOFT — set DETERMINISM_RUN_2_REPORT to a second run's path
det_path = os.environ.get("DETERMINISM_RUN_2_REPORT")
if det_path and os.path.exists(det_path):
    with open(det_path) as f2: t2 = f2.read()
    rule_ids_2 = set()
    for p in RULE_PREFIXES:
        rule_ids_2.update(re.findall(rf"\b{p}\b", t2))
    diff = rule_ids ^ rule_ids_2
    add("SOFT", "determinism_rule_set", f"symmetric_diff={sorted(diff)}", len(diff) == 0, note="LLM-judged predicate variance")

fail = 0
print(f"{'severity':8} {'metric':30} {'value':30} {'flag':>6}  note")
for sev, name, val, flag, note in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:8} {name:30} {str(val)[:30]:30} {flag:>6}  {note}")
sys.exit(1 if fail else 0)
PY
```

If exit non-zero → STOP, do not persist. Report failures, propose specific fixes, ask user.

### Layer B — adversarial critic dispatch (blind, recall-framed)

**Layer-B-Gate.** Per `docs/skill-verification-architecture.md`, AUDIT
output is structured extraction when predicates are mechanical. Layer B
fires ONLY when ≥30% of this skill's predicates require LLM judgment
(closed-set classification, taxonomy ambiguity, behavioral-signal
detection). For pure-mechanical audits (file exists / regex matches /
exit code only), SKIP Layer B and rely on Layer A + Layer C alone.
Document the gate decision in the report frontmatter as
`layer_b_fired: true|false (rationale)`.

The critic compares the produced report against a multi-source target assemblage: `sw_vers -productVersion` output, the `security find-internet-password` / `find-generic-password` listing for the `Claude Code-credentials` service, and the active-session count from `ps -ax`. Its job is to find KCH-/SES- firings the audit MISSED or that it ADDED without grounded evidence. Adversarial framing — not "rate quality" — is the layer that catches false positives and false negatives (see template F2, F3).

```
Agent({
  description: "Adversarial audit-mcp-auth critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind audit-critic. Two artifacts are attached: " +
    "A: source assemblage — sw_vers output, security find-generic-password " +
    "listing for service 'Claude Code-credentials', and ps -ax output for " +
    "claude processes (concatenated, labelled). " +
    "B: the audit report produced from A (Markdown with frontmatter, " +
    "Status, and KCH-/SES- findings). " +
    "Neither label tells you which artifact came first.\n\n" +
    "1. For each KCH-/SES- finding in B, locate the corresponding evidence " +
    "in A and classify as:\n" +
    "   GROUNDED — evidence in A matches rule-id and severity\n" +
    "   WEAKENED — evidence in A is weaker than the asserted severity\n" +
    "   ADDED   — no evidence in A supports the finding (false positive)\n\n" +
    "2. Scan A for #45551 signal patterns the report did NOT flag. The " +
    "catalog is KCH-1 (entry size > 2010 bytes), KCH-2 (JSON parse failure " +
    "or missing claudeAiOauth key), SES-1 (>5 concurrent claude processes). " +
    "If A shows a pattern matching any catalog rule but B has no finding, " +
    "classify DROPPED.\n\n" +
    "3. Report ONE block per item:\n" +
    "   [GROUNDED|WEAKENED|ADDED|DROPPED]: rule-id\n" +
    "   evidence_in_A: \"<short quote or line ref>\"\n" +
    "   evidence_in_B: \"<short quote or finding-id>\"\n" +
    "   reason: <≤2 sentences>\n\n" +
    "Do not rate quality. Do not praise coverage. Do not write a summary. " +
    "Report under 500 words.\n\n" +
    "A:\n<paste sw_vers + security listing + ps -ax output>\n\n" +
    "B:\n<paste $REPORT contents>"
})
```

**Order-swap mandate**: dispatch a second time with labels reversed (`A`=report, `B`=source). Take the union of items flagged across both runs, de-duped by `rule-id × evidence_in_A`. Position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791).

### Layer C — binary rubric reconciliation (CheckEval-style)

Six yes/no dimensions specialized to this skill. CheckEval (arXiv:2403.18771) reports +0.45 inter-evaluator agreement for binary vs. Likert. Any `NO` blocks report persistence until resolved.

```
D1 STATUS_VOCAB_CONFORMANT   The `Status` line in the body and any
                              summary[].status in frontmatter belong to
                              the closed set {healthy, warning, critical}.
                              Catches status-enum drift (F5).

D2 EVIDENCE_GROUNDED          Every KCH-/SES- finding's Evidence cites a
                              concrete byte count, parse error, or process
                              count that resolves against the source
                              assemblage (sw_vers / security / ps). Layer A
                              redaction passed AND Layer B yielded zero
                              ADDED items. Catches false-positive
                              misclassification (F2) and fabricated
                              evidence (F9).

D3 TAXONOMY_DISJOINT          No two findings cite distinct rule-ids for
                              the same evidence span (e.g., same byte
                              count flagged as both KCH-1 and KCH-2). Rule
                              IDs stay within the closed catalog
                              {KCH-1, KCH-2, SES-1}. Catches F4.

D4 SEVERITY_CALIBRATED        Each rule-id appears with a single severity
                              across the report (KCH-1=H by detector-rules,
                              KCH-2=H, SES-1=M). Layer A rule_severity_stable
                              passed AND Layer B yielded zero WEAKENED
                              items. Catches F8.

D5 RULE_CATALOG_COMPLETENESS  Layer B critic surfaced ZERO DROPPED items —
                              no #45551 signal in the source assemblage
                              went unflagged. THIS IS THE LOAD-BEARING
                              DIMENSION for this skill (per audit-template
                              §audit-mcp-auth). Catches F1, F3.

D6 DISCOVERY_PRECISION        Predicate-class output → trivially YES
                              (this skill does not emit a discovery-style
                              candidate ledger; D6 is satisfied by virtue
                              of the closed-catalog shape).
```

Layer-A row → Dimension mapping:
- `frontmatter_present`, `required_frontmatter_keys`, `status_in_vocab` → D1
- `host_platform_present`, `keychain_entry_redacted` → D2
- `schema_version_pinned`, `severity_tokens_valid` → D1/D4
- `rule_severity_stable` → D4

Layer-B item → Dimension mapping:
- `ADDED` → D2 NO
- `WEAKENED` → D4 NO
- `DROPPED` → D5 NO
- `GROUNDED` → no impact (expected)

### Reconciliation outcomes

- **All STRICT pass + zero ADDED/WEAKENED/DROPPED** → proceed to report persistence under `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Any STRICT fail OR any ADDED/WEAKENED/DROPPED** → restore inline: drop fabricated findings, re-classify weakened severity, add dropped rule firings. Re-run Layer A on the patched report. Max 2 iterations. If still failing after iteration 2, surface to user with the full ledger and DO NOT persist the report.
- **Only SOFT warnings** (e.g., `determinism_rule_set` symmetric-diff non-empty) → report as a footnote in the audit report ("This audit was non-deterministic across N runs; finding set may vary"), then proceed.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Macroscale ground-truth absence on Keychain audits** — the skill reads macOS Keychain state but has no oracle for "this entry is legitimate vs. corrupted-by-#45551". The pipeline verifies that the rule fired on the right evidence (size, JSON shape, process count), NOT that the rule's premise (the #45551 bug class) is operative on this host. A 2050-byte entry from a non-Claude OAuth app would still fire KCH-1 because the threshold is the only deterministic signal available. Documented per audit-template.md Acknowledged Residual #6.
2. **#45551 bug-class drift** — KCH-1's 2010-byte threshold and SES-1's >5-process threshold are empirical, drawn from the GitHub issue's reproducer set. If Anthropic patches the libsecurity buffer limit or changes the concurrency model, the catalog drifts silently; no in-skill regression mechanism detects this. Mitigation: maintainer refresh of `references/detector-rules.md` on the repo's 90-day rhythm.
3. **Multi-host audit invisibility** — a workspace-wide #45551 event manifests across multiple machines simultaneously, but this skill runs locally on one host. A clean local report does not imply workspace-wide health. Cross-host correlation is out of scope.
4. **Redaction-by-length false negatives** — the keychain_entry_redacted STRICT row catches Base64 strings >256 chars but does not catch shorter accidental leakage (e.g., a 200-char OAuth token snippet). The detector is necessary-not-sufficient; reviewer must spot-check evidence excerpts.

The Output report MUST list which residual classes apply to passages the critic flagged as `UNCERTAIN`, so the user has one last human-glance opportunity before any remediation action is recommended.

## Hard Rules

- Never write to the keychain.
- Never invoke `claude /mcp` subcommands — this skill audits, does not
  remediate.
- Never echo full keychain entry contents to user-visible output —
  redact via `head -c 200 | base64` for evidence snippets.
- Never run on non-macOS — silently no-op.
