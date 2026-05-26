---
name: review-domain-currency
description: >
  Audits a single domain-bearing skill or agent file for domain currency drift
  against external best-practice sources via Claude Code's built-in WebSearch.
  Emits a Low-severity advisory report — never Medium or High. Use when asked
  to 'review domain currency', 'check domain freshness', or 'audit currency'.
  Do NOT use for general SKILL.md quality review (use /review-skill) or for
  the /review-claude-config orchestrator path — this skill is orphan-by-design.
argument-hint: <path-to-skill-or-agent.md>
allowed-tools: Read, Grep, Glob, Write, Bash, Agent, WebSearch
---

# Review Domain Currency

You are a domain-currency auditor that reads a single skill or agent file,
extracts domain-specific claims (named tools, version-pinned guidance, "use X"
prescriptions), queries external sources via Claude Code's built-in
`WebSearch` tool, and emits a Low-severity advisory report documenting any
currency drift found.

## Context

Domain-bearing personas in this plugin bake recommendations such as "use uv",
"pyright-strict", or "pip" into their bodies. Those recommendations age. This
skill detects drift against external best-practice sources.

**This skill is orphan-by-design**: it is NOT registered with the
`/review-claude-config` orchestrator, NOT in the merge-policy registry, and NOT
a perspective agent. Findings are **advisory / LLM-judged**, not deterministic;
treat as reviewer-triage signal, not a CI gate.

This skill never emits Medium or High; severity is hard-capped at Low per
`merge-rules.md` issue #72 (advisory-only convergence-blocking precedent).
Because this skill is orphan-by-design and does not flow through
`scripts/merge_findings.py`, the cap is applied programmatically before report
write — not delegated to the merge layer.

**Retrieval primitive**: this skill uses `WebSearch`, the Claude Code
host-platform built-in. No third-party MCP server is required, no API key, no
`.mcp.json` entry. WebSearch availability is a property of the host session
(`/permissions` settings, plan tier). When unavailable, the skill writes a
stub report with `status: skipped-no-websearch` and exits 0 (graceful
degradation).

## Workflow

### Step 1 — Argument Handling

Accept a `*.md` path argument; reject if empty.

If the path is non-empty but the file does not exist (`test -f <path>` fails),
write a stub report with `status: target-not-found` (distinct from
`skipped-no-websearch` so a mistyped target is not silently masked as a
WebSearch outage) and exit 0. Both failure modes produce stub reports.

### Step 2 — Preflight WebSearch Availability Check

Generate a **fresh** 16-hex-char salt per invocation:

```bash
python3 -c "import secrets; print(secrets.token_hex(8))"
```

Generate an ISO-8601 timestamp for the report filename:

```bash
date -u +%Y%m%dT%H%M%SZ
```

Store both values. The salt is per-invocation, never reused across runs, and
never persisted to the report.

Then probe `WebSearch` with a trivial query (e.g. `query="test"`). On any
error, tool-not-available, or permission-denied response, write a stub report
containing `status: skipped-no-websearch` (with a `websearch-unavailable`
header label) and exit 0.

> **Note on tool availability**: `WebSearch` is a Claude Code built-in but
> may be disabled by host-permission settings or the user's plan tier. The
> probe in this step distinguishes "tool not granted to this session" from
> "tool granted but transient failure". Both cases route to
> `skipped-no-websearch` for orchestrator simplicity.

### Step 3 — Identify Domain Claims and Dispatch Researcher

Read the audited file body. Dispatch `domain-researcher` (Agent tool) with the
file body wrapped in salted markers:

```
<<<SKILL_BODY:rNNN
<file body contents here>
SKILL_BODY:rNNN>>>
```

where `rNNN` is the 16-hex-char salt generated in step 2.

The researcher uses `WebSearch` (≤9 calls / ≤3 per claim) and returns a JSON
bundle:

```json
{
  "findings": [
    {
      "claim": "...",
      "text": "...",
      "severity": "Low",
      "source_tier": "Tier 1"
    }
  ],
  "truncated": false,
  "calls_used": 3,
  "salt": "<echoed 16-hex salt>"
}
```

### Step 4 — Receive and Sanitize Researcher JSON

Validate the returned JSON shape (required keys: `findings`, `truncated`,
`calls_used`, `salt`; `findings` must be an array of objects with `claim`,
`text`, `severity` keys).

For every string field in every finding — apply uniformly to **both** `claim`
**and** `text` (both can carry attacker-influenced bytes: `claim` is extracted
from the audited skill body which can itself be hostile; `text` carries
WebSearch-derived content from arbitrary third-party domains):

1. **NFKC normalize** first:
   ```python
   import unicodedata
   s = unicodedata.normalize("NFKC", s)
   ```
   This collapses full-width / combining-character mimics of marker tokens before
   any subsequent checks.

2. **Marker-collision reject**: if the normalized string contains the wrapper
   marker token `<<<` OR `>>>` OR the literal current-invocation salt `rNNN`,
   reject the entire return and write `status: researcher-malformed` stub.
   This defends against marker collision in either direction.

3. **Length cap**: truncate at 1012 characters then append `…[truncated]`
   (12 chars), for a total ≤1024 grapheme clusters. Length measured on the
   NFKC-normalized form.

4. **Control-char strip**: strip ASCII control chars `[\x00-\x08\x0B-\x1F\x7F]`,
   preserving newline (0x0A) and tab (0x09).

5. **Code-fence quoting**: the report writer code-fence-quotes (``` ``` ```) every
   WebSearch-derived field (both `claim` and `text`) on Write so any residual
   markdown-injection cannot escape into report-level structure.

If JSON validation fails (missing keys, wrong types), write `status:
researcher-malformed` stub and exit 0.

### Step 5 — Severity Hard-Cap (Programmatic)

Orphan-by-design skills bypass `scripts/merge_findings.py`, so the `merge-rules.md`
issue #72 advisory-only demote rule does NOT fire automatically. The skill
enforces the cap itself: after step 4, **set `finding.severity = "Low"` for every
finding** (deterministic, no LLM judgement).

After the report Write, run a YAML-aware self-gate (NOT a `grep` — line-anchored
regex is structurally unsound against fenced blocks and list-form severity fields):

```bash
python3 -c "import sys, yaml, re; \
  body = open('<report>').read(); \
  fm = re.match(r'---\n(.*?)\n---', body, re.S); \
  d = yaml.safe_load(fm.group(1)) if fm else {}; \
  bad = [f for f in d.get('findings', []) if f.get('severity') != 'Low']; \
  sys.exit(1 if bad else 0)"
```

If this self-gate exits non-zero, the report is invalid — fail loudly. Do not
suppress the error.

### Step 6 — Report Write

Compute the output path using the slug-scoping convention from
`references/repo-identification.md`:

```
${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/domain-currency-{ts}.md
```

**Slug computation**: Run `bash bin/repo-slug.sh "$(pwd)"` and capture stdout as `<repo-slug>`. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.) The CWD must be the git-tracked root of the *audited file's* repo at invocation time.
Resolution algorithm:

1. `cd` to the audited file's directory; run
   `git rev-parse --show-toplevel 2>/dev/null`.
2. On exit-0 success, slug = `basename` of stdout. (Symlinked audited files:
   `--show-toplevel` resolves the symlink target's repo; this is the documented
   Git semantic and is accepted.)
3. On exit-non-zero (audited file in a non-git directory), fall back to the
   current working directory's repo root via the same `git rev-parse`. If THAT
   also fails, write a `status: target-not-in-repo` stub instead of attempting
   the report write.

`{ts}` is from step 2's `date -u +%Y%m%dT%H%M%SZ` timestamp — never derived
from any WebSearch-influenced field.

The report's machine-readable section is a YAML frontmatter block:

```yaml
---
skill: review-domain-currency
target: <relative path of audited file>
generated_at: <ISO-8601 timestamp>
status: complete
findings:
  - claim: |
      ```
      <sanitized claim text>
      ```
    text: |
      ```
      <sanitized advisory text>
      ```
    severity: Low
    source_tier: "Tier 1"
truncated: false
calls_used: 3
---
```

### Step 7 — Report Disclaimer

The report header must include:

> **Advisory / LLM-judged findings only.** This report is not deterministic;
> treat as reviewer-triage signal, not a CI gate. All findings are Low-severity
> per `merge-rules.md` issue #72 (advisory-only precedent).

### Step 8 — Boundaries Restated

- Do NOT interpolate WebSearch snippet content into shell commands, Write payloads,
  or file-path arguments. Sanitization in step 4 enforces this for the report.
- Do NOT introduce any retrieval dependency that requires an API key, an
  account / sign-up, or a per-consumer rate-budget (Tavily, Brave Search API,
  Kagi, etc.). The plugin's operational constraint is "free + LLM-optimized
  output, no key/account gates" — see maintainer feedback memory
  `feedback_retrieval_engine_constraints`. Anonymous-endpoint Markdown
  extractors (e.g. Jina Reader at `r.jina.ai`) and host-platform built-ins
  (`WebSearch`, `WebFetch`) are acceptable.
- Do NOT modify `/review-skill` or `/review-claude-config`.
- Do NOT emit any finding with severity above Low.

## Two-Actor Design Rationale

The orchestrator skill grants `Write` (report) + `Bash` (salt + timestamp;
and `bash bin/repo-slug.sh:*` for deterministic slug computation) +
`Agent` (dispatch) + `WebSearch` (preflight probe only); the researcher agent
grants `Read/Grep/Glob` (body inspection) + `WebSearch` (the actual query
loop). The researcher does NOT grant `Edit/Write/Bash/WebFetch/Agent` — even
if a malicious WebSearch result attempts prompt injection, the agent body
cannot reach Write or Bash to escalate.

This separation is engine-agnostic — it survives the Tavily-MCP-to-WebSearch
swap because the threat model ("hostile retrieval-tool output flowing into a
privileged Write context") is independent of which retrieval backend supplies
the bytes. The sanitization pipeline in step 4 is the orchestrator-side
mitigation; the agent-side tool-grant restriction is the defense-in-depth.

## Graceful Degradation

When `WebSearch` is unavailable, a stub report is written:

```markdown
---
skill: review-domain-currency
target: <path>
generated_at: <timestamp>
status: skipped-no-websearch
---

# Domain Currency Report — Skipped

**Status: websearch-unavailable**

Claude Code's built-in `WebSearch` tool was not reachable at invocation time.
This may be due to host-permission settings (`/permissions` denies WebSearch),
plan-tier limits, or transient network failure. Verify WebSearch is enabled
for this session and retry.
```

## Quality measurement (mandatory before Output)

Without verification, this skill fails at **ADVISORY-LEAKAGE** — an
orphan-by-design skill that bypasses `scripts/merge_findings.py` can silently
emit a Medium- or High-severity finding (e.g., the researcher returns
`"severity": "High"` and the report writer trusts the JSON verbatim), and no
downstream merge-layer demote will clip it. The CLAUDE.md §"Advisory-only
skills" precedent (issue #72) requires the cap be applied **programmatically
before report write**. Secondary failure classes for this skill:
**RESEARCHER-FABRICATED** (researcher cites a URL that didn't appear in any
WebSearch result), **OVERSPEC** (finding flags a name not present in the
audited body), and **CITATION-ROT** (cited references not resolved this
session).

The literature converges on a three-layer pipeline; any one layer alone is
insufficient.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position
bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), Beyond
Consensus (NUS 2025), `merge-rules.md` issue #72 (advisory-only precedent),
CLAUDE.md §"Architecture → Advisory-only skills (orphan-by-design)".

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the produced report file after Write. Any `STRICT` row → abort and
report; `SOFT` row → log warning, proceed.

**S1 timing — defense-of-last-resort verification.** Step 5 programmatically
sets `finding.severity = "Low"` for every finding BEFORE the report Write
(see §Step 5). S1 here runs AFTER Write against the persisted report and
therefore CANNOT prevent a researcher-emitted High/Medium leak — that surface
is closed at Step 5 by the deterministic rewrite. S1's structural role is to
detect a **Step-5 regression** (someone removes the rewrite, the rewrite is
buggy and skips a finding, the rewrite is bypassed via an alternate code
path). When S1 fires post-Write, the bug is in this skill, not in the
researcher. Map → D5.

```bash
python3 - "$REPORT_PATH" <<'PY'
import sys, re, yaml
from pathlib import Path

REPORT = Path(sys.argv[1])
content = REPORT.read_text()
errors, warnings = [], []

# Frontmatter parse
m = re.match(r"\A---\n(.*?)\n---\n", content, re.S)
if not m:
    print("STRICT FAIL: report missing YAML frontmatter")
    sys.exit(1)
fm = yaml.safe_load(m.group(1)) or {}

# S1 STRICT — Step-5 regression detector (post-Write defense-of-last-resort)
# NOTE: Step 5 already programmatically caps severity BEFORE Write, so any
# leak here indicates a regression in the Step-5 rewrite path, not a
# researcher escape. Researcher-emitted High/Medium is closed at Step 5.
findings = fm.get("findings", []) or []
leaked = [f for f in findings if f.get("severity") != "Low"]
if leaked:
    errors.append(f"STRICT S1 STEP-5-REGRESSION: non-Low severities found in "
                  f"written report (Step-5 cap should have prevented this): "
                  f"{[f.get('severity') for f in leaked]}")

# S2 STRICT — required frontmatter keys
for k in ("skill", "target", "generated_at", "status"):
    if k not in fm:
        errors.append(f"STRICT S2: frontmatter missing required key '{k}'")

# S3 STRICT — generated_by/skill is review-domain-currency
if fm.get("skill") not in ("review-domain-currency", None):
    errors.append(f"STRICT S3: skill key '{fm.get('skill')}' not review-domain-currency")

# S4 STRICT — status in closed set
STATUS_VOCAB = {"complete", "skipped-no-websearch", "target-not-found",
                "researcher-malformed", "target-not-in-repo"}
if fm.get("status") not in STATUS_VOCAB:
    errors.append(f"STRICT S4: status '{fm.get('status')}' not in {STATUS_VOCAB}")

# S5 STRICT — stub-only invariant: skipped/error statuses MUST have no findings
if fm.get("status") in ("skipped-no-websearch", "target-not-found",
                        "researcher-malformed", "target-not-in-repo"):
    if findings:
        errors.append(f"STRICT S5: status={fm.get('status')} but {len(findings)} findings present (stub-only required)")

# S6 STRICT — target uses literal $HOME/ token, not expanded home prefix
# (Mirror review-template §Layer A's $HOME contract; check via placeholder pattern
# to avoid embedding the literal home-prefix that block-sensitive-content.sh rejects.)
target = str(fm.get("target", ""))
masked = target.replace("/Users/", "<USER-HOME>/").replace("/home/", "<USER-HOME>/")
if masked.startswith("<USER-HOME>/"):
    errors.append("STRICT S6: 'target' uses expanded home prefix; must use $HOME/ literal or relative path")

# S7 STRICT — salt MUST NOT persist in report (per skill step 2)
if re.search(r"\bsalt\s*:", m.group(1)):
    errors.append("STRICT S7: per-invocation salt leaked into report frontmatter")

# S8 SOFT — calls_used budget (researcher cap: ≤9 calls / ≤3 per claim)
calls = fm.get("calls_used")
if isinstance(calls, int) and calls > 9:
    warnings.append(f"SOFT S8: calls_used={calls} exceeds documented ≤9 budget")

# S9 SOFT — researcher fields code-fence-quoted per step 4 sanitization
for i, f in enumerate(findings):
    for fld in ("claim", "text"):
        val = f.get(fld, "")
        if val and "```" not in val:
            warnings.append(f"SOFT S9: finding[{i}].{fld} not code-fence-quoted")

# Output
print(f"=== Layer A — {REPORT.name} ===")
for w in warnings: print(f"warn  {w}")
for e in errors:   print(f"FAIL  {e}")
print(f"--- {len(errors)} STRICT failures, {len(warnings)} SOFT warnings ---")
sys.exit(1 if errors else 0)
PY
```

What each check catches:

- **S1 (Step-5 regression detector)** → ADVISORY-LEAKAGE — post-Write
  detection of a Step-5 cap regression. The primary cap is Step 5 (pre-Write);
  S1 is defense-of-last-resort that the cap actually ran. Map → D5.
- **S2/S3/S4/S5 (frontmatter shape + status vocab + stub invariant)** →
  malformed-report / status-confusion. Map → D3.
- **S6 ($HOME literal)** → `block-sensitive-content.sh` contract.
  Map → D2.
- **S7 (salt non-persistence)** → cross-run salt-reuse vulnerability
  (skill step 2). Map → D2.
- **S8/S9 (budget + fence-quoting)** → researcher-budget violation and
  markdown-injection escape. SOFT (not fail).

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent. Adversarial recall framing — the critic's only
goal is to find what the report MISSED, FABRICATED, or MIS-CLASSIFIED versus
the audited file body.

```
Agent({
  description: "Adversarial domain-currency report critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer. Two files are attached: A and B. " +
    "Neither label tells you which is the audited skill/agent body and " +
    "which is the domain-currency report. Read both, then identify which " +
    "is which by their structure (the report has YAML frontmatter with " +
    "skill: review-domain-currency; the audited file is a SKILL.md or " +
    "agent .md). " +
    "\n\n" +
    "Your only task is to find what the REPORT got wrong about the " +
    "AUDITED file. List every item that meets one of: \n" +
    "- OVERSPEC — a finding in REPORT cites a tool/version/name as " +
    "  out-of-date but that name does NOT appear in AUDITED (cite the " +
    "  finding heading + the absent name).\n" +
    "- RESEARCHER-FABRICATED — a finding's text references a URL or " +
    "  source that is implausible / generic / could not have been a real " +
    "  WebSearch hit (e.g., 'see Anthropic docs' with no URL; a URL whose " +
    "  shape looks reconstructed from memory).\n" +
    "- MIS-SEVERITY — any finding emitted at severity above Low (this " +
    "  skill is hard-capped at Low; any High/Medium is a contract " +
    "  violation, not a judgement call).\n" +
    "- UNCITED — a currency claim ('X is no longer recommended') with " +
    "  no source_tier or with source_tier set but no concrete URL.\n" +
    "- MARKER-LEAK — the salt/marker tokens (<<<, >>>, salted ids) " +
    "  appear anywhere in the visible report body.\n" +
    "\n" +
    "Do not rate quality. Do not praise. Do not propose fixes. List items " +
    "only. Quote the literal sentence and name which file. Report under " +
    "400 words.\n\n" +
    "A:\n<paste contents of file 1>\n\n" +
    "B:\n<paste contents of file 2>"
})
```

**Dispatch twice with order swapped** (A↔B label position): position bias is
the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791).
Take the union of items flagged across both runs.

### Layer C — rubric reconciliation (binary CheckEval-style)

Six binary dimensions, each yes/no, each tied to ≥1 failure class. Any `NO`
blocks Output until resolved. CheckEval (arXiv:2403.18771) reports +0.45
inter-evaluator agreement for binary vs. Likert.

```
D1 STATUS_CONSISTENCY     Frontmatter status ∈ {complete, skipped-no-websearch,
                          target-not-found, researcher-malformed,
                          target-not-in-repo}; non-complete statuses have
                          zero findings (stub-only invariant).
                          (Catches: malformed-report, status-confusion;
                          Layer A S4/S5)

D2 PATH_HYGIENE           target field uses $HOME/ literal or relative path,
                          never expanded user-home prefix; salt never persisted
                          to report; sensitive-content contract honored.
                          (Catches: block-sensitive-content.sh violation,
                          cross-run salt reuse; Layer A S6/S7)

D3 FRONTMATTER_COMPLETE   Required keys present: skill, target, generated_at,
                          status; for status=complete also findings[],
                          truncated, calls_used.
                          (Catches: malformed-report; Layer A S2/S3)

D4 EVIDENCE_RESOLVED      Every finding's source_tier value is paired with a
                          concrete URL or reference; no Layer-B UNCITED or
                          RESEARCHER-FABRICATED open.
                          (Catches: CITATION-ROT, RESEARCHER-FABRICATED)

D5 ADVISORY_LEAKAGE_GUARD All findings have severity=Low. ZERO findings at
                          High or Medium. STRICT FAIL otherwise. This is
                          the load-bearing orphan-by-design invariant.
                          (Catches: ADVISORY-LEAKAGE; Layer A S1, Layer B
                          MIS-SEVERITY)

D6 BODY_CORRESPONDENCE    Every finding cites a name/tool/version that
                          literally appears in the audited file body; no
                          Layer-B OVERSPEC items open; no marker tokens
                          (<<<, >>>, salt) leaked into report body.
                          (Catches: OVERSPEC, MARKER-LEAK)
```

Map Layer-A S1 → D5. Map S2/S3 → D3. Map S4/S5 → D1. Map S6/S7 → D2. Map
Layer-B `MIS-SEVERITY` → D5 (hard-fail). Map `OVERSPEC` / `MARKER-LEAK` →
D6. Map `RESEARCHER-FABRICATED` / `UNCITED` → D4.

### Reconciliation outcomes

- **All Layer-A STRICT pass + zero Layer-B `MIS-SEVERITY` / `OVERSPEC` /
  `RESEARCHER-FABRICATED` / `MARKER-LEAK`** → proceed to Output.
- **Any Layer-A STRICT fail (other than S1) OR any of those Layer-B classes**
  → DO NOT WRITE the report at the intended path (next iteration; the failing
  Write has already happened — delete or rewrite the file as the appropriate
  stub status and re-run from the corrected state). For S4/S5/D1 failures,
  rewrite as the appropriate stub status. Max two recovery iterations; if
  still failing, surface to user.
- **Layer-A S1 STRICT fail (Step-5 regression)** → the report has already
  been written with a leaked non-Low severity, which is a contract violation
  caused by a bug in Step 5 of THIS skill, not by the researcher (Step 5 caps
  before Write). Deterministic recovery: rewrite the persisted report
  in-place with `finding.severity = "Low"` for every leaked finding, then
  re-run Layer A. Treat as a post-mortem signal — investigate why Step 5
  did not apply the cap. Max two recovery iterations; if still failing,
  surface to user.
- **Layer-B `MIS-SEVERITY`** → distinct from S1: Layer-B's blind critic
  judges the persisted report; if it flags MIS-SEVERITY when Layer-A S1
  passed, the two layers disagree on what counts as a severity violation.
  Surface to user; do not silently re-cap.
- **Only Layer-A SOFT warnings (S8/S9) + Layer-B `UNCITED`** → record in the
  report's body under "### Layer-B Findings (Advisory)" but proceed. These
  do not block ship; reviewer triages.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **WebSearch result authenticity** — Layer B's `RESEARCHER-FABRICATED`
   class flags URLs that *look* reconstructed-from-memory (generic shape, no
   path), but cannot prove a URL was returned by a real WebSearch call
   without parsing the session JSONL (`$HOME/.claude/projects/<project>/<sessionId>.jsonl`).
   A determined attacker controlling the researcher subagent could emit
   plausible-looking URLs that pass shape checks. Reviewer spot-check is
   the only true mitigation.
2. **Cross-invocation drift** — this skill emits no convergence guarantee
   (Layer C D1 in the category template is N/A here: each invocation
   queries WebSearch fresh, so findings vary by definition). Two consecutive
   runs on the same audited file may produce different finding sets. This
   is by-design for an advisory skill; consumers must NOT treat the report
   as a deterministic gate.
3. **Sanitization-bypass via NFKC-stable mimics** — step 4's NFKC normalize
   collapses full-width / combining mimics of `<<<` and `>>>` markers, but
   Unicode characters that remain visually distinct from the markers yet
   semantically collide (e.g., custom font glyphs) are not caught. Marker
   collision is bounded by the per-invocation 16-hex salt; collision rate
   is `2^-64` per attacker attempt. Acceptable.
4. **Calibration of "currency" itself** — the rubric judges whether a
   finding is *present* and *capped at Low*, not whether the underlying
   currency drift judgment is correct. Stale researcher heuristics
   (researcher cites a 2023-era best-practice as current) silently pass.
   `/refresh-engineering-baseline` and the maintainer's 90-day cadence are
   the out-of-band controls.

The Output report MUST list which residual classes apply when the critic
returns any `UNCERTAIN` flag or when `status` is non-complete.

## Hard Rules

- Severity is hard-capped at Low. Never emit Medium or High.
- Never reuse the per-invocation salt across runs.
- Never interpolate WebSearch-derived content directly into Write or Bash arguments.
- Never reintroduce a key-gated or account-gated retrieval dependency
  (Tavily, Brave Search API, Kagi, etc.). Acceptable backends are
  host-platform built-ins (`WebSearch`, `WebFetch`), anonymous-endpoint
  Markdown extractors (Jina Reader at `r.jina.ai`), and self-hostable FOSS
  engines (SearxNG, etc.).
