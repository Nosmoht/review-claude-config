# Roadmap: review-claude-config — Consolidated Prioritization (2026-04-19, rev4)

## Context

Consolidation of four input streams:
1. Internal backlog (IDEAS.md, PROGRESS.md, ~60 open GitHub issues).
2. Claude Code feature drift Feb–Apr 2026 (Opus 4.7 shipped 2026-04-16 with new tokenizer and `xhigh` effort; /ultrareview GA same day; 26-event hook catalog documented; MCP tool-search/lazy-loading + elicitation + `_meta` annotations; Plugin system + Marketplace).
3. Aperant (AndyMik90/Aperant) pattern adoption: multi-perspective review, shared-prefix KV-cache, 3-tier structured-output recovery, atomic writes, cache-status labels, Trust-or-Escalate cost model.
4. Deep per-domain web research (11 domain agents against Tier-1 sources) plus three-perspective plan review (Prompt-Engineering, Context-Engineering, Agent-Harness) — all findings integrated into rev4.

**Revision history:**
- rev1: initial draft.
- rev2: plan review round 1 → P1.4 promoted to P0.5, P1.3 demoted, baseline-serialization rule, missing IDEAS items.
- rev3: 11-agent deep research → agent frontmatter 8→15 fields, 26-event hook catalog confirmed, MCP April-2026 security disclosure added, two 9-month-old CRITICAL bugs (#39523, #45551) added as P0.6, multi-perspective set corrected to Clarity/Correctness/Integration, Trust-or-Escalate replaces Selective-k=3, KB Artifacts Appendix with 14 research files.
- **rev4 (this)**: plan review round 2 integrated from three critical reviewers (PE/CE/Agent-Harness). 8 High-Severity findings resolved: subagent definition location, per-perspective frontmatter matrix, tool-grants & 5-tier combo-check, plugin injection-risk controls, binary-verifiable rubric items, explicit domain-ownership in sub-agent prompts, `/validate-primitive-dependencies` as P0/P1 exit, new P0.0 for BUDGETS-map pre-provisioning, CLAUDE.md §Research References extracted to `docs/research-index.md`, mid-session rubric-freeze rule, apply-* TaskCreate grants + delegation visibility, cache-churn operative rule. 12 Medium and 7 Low findings also integrated.

## Current State Snapshot

Implemented (verified 2026-04-19): 19 public slash-commands + 3 repo-internal skills; 7 hooks; coverage across all primitives; 10 docs files; 36 research topic directories; dependency integrity HEALTHY.

**Review agents & suggest agents clarification:**
- As slash-commands → fully complete. All 8 `/review-*`, all 7 `/suggest-*`/`/audit-*` implemented. 6 skills from 2026-04-04 suggest-report all present.
- As sub-agents within review workflows → **still open**. P1.1 addresses this.

## Claude Code Feature Drift — Corrected Catalog (Feb–Apr 2026)

Tier labels: T1 (official Anthropic/GitHub), T2 (engineering blogs with detail).

| # | Feature | Tier | Impact |
|---|---------|------|--------|
| F1 | `.claude-plugin/plugin.json` + Marketplace. 3 required fields + 12 optional. Components MUST live in plugin root. `/plugin:skill` namespacing mandatory. `claude plugin validate` CLI. | T1 | P0.4 new /review-plugin |
| F2 | 15 agent frontmatter fields documented: `name, description, model, color, tools, disallowedTools, maxTurns, background, isolation, memory, initialPrompt, mcpServers, skills, hooks, permissionMode, effort`. | T1 | P0.1 /review-agent rubric + F8 Opus 4.7 tier |
| F3 | 26-event hook catalog with CLI-min-version mapping (`PostToolUseFailure` v2.1.76, `CwdChanged`/`FileChanged` v2.1.83, `TaskCreated` v2.1.84, `PermissionDenied` v2.1.89). | T1 | P0.2 /review-hook + new verify_hook_events.py |
| F4 | MCP tool-search/lazy-loading (auto at 10K desc tokens; 85% savings), Elicitation (form/url modes), `_meta["anthropic/maxResultSizeChars"]`, `.mcp.json` new fields. **April 2026 security disclosure**: ~200K vulnerable servers; Anthropic declined architectural change. | T1 | P0.3 /review-mcp-server rubric + security scan |
| F5 | Auto-memory v2.1.59+: MEMORY.md per repo, first 200 lines/25KB in system prompt. | T1 | P2.3 /audit-memory-hygiene patch |
| F6 | /ultrareview GA 2026-04-16 (v2.1.111). $15–25/review. **No programmatic API trigger**. Not on Bedrock/Vertex/Foundry. | T1 | P3 only — at most emit a recommendation |
| F7 | Monitor tool v2.1.98+: streaming stdout. Bugs #50258 (notification flooding), #45976 (tmux detachment). | T1 | P3 until bugs fixed |
| F8 | Opus 4.7 (2026-04-16). `xhigh` effort (Opus only). **Breaking**: extended thinking budgets removed, sampling params (`temperature`/`top_p`/`top_k`) removed, new tokenizer (~35% more tokens vs 4.6). Task Budgets beta. | T1 | Merged into P0.1 |
| F9 | #41259 permission cache reload bug still OPEN. #39523 ([META] bypass permissions fundamentally broken, 9 months, CRITICAL). | T1 | P0.6 detector |
| F10 | #45551 MCP OAuth credential-store corruption — Team-plan concurrent sessions wipe `claudeAiOauth` keychain entry. | T1 | P0.6 detector |
| F11 | #50655 plugin manifest git-index leak in pre-commit hooks. | T1 | P3 niche |

## Aperant-Adopted Patterns (Refined)

| Pattern | Effort | Payoff | Adopted in | Refinement |
|---------|--------|--------|------------|------------|
| Multi-perspective subagent review (Clarity/Correctness/Integration for skill/agent/rule review) | Medium | High | P1.1 | Coverage 45% → 94% (arXiv:2512.16272). |
| Shared-prefix + per-item suffix KV-cache | Low | Medium | P1.1 (bundled) | Opus minimum 4,096 tokens; Sonnet 1,024. Break-even ~12 hits. 90% savings on hit. |
| 3-tier structured-output recovery | Low | Medium-High | P1.2 | Tier-2 extraction ~98% success with minimal flat schema; total failure <2%. |
| Atomic file writes (write-to-tmp + rename + retry) | Low | Low-Medium | P2.7 | Aperant PR #1785. |
| Cache-status labels (CACHED/STALE/FAILED/RUNTIME_RESEARCH) | Low | Low-Medium | P2.4 | 4 states. |
| Trust-or-Escalate (arXiv:2407.18370) | Medium | High | P1.1 | 1.35× cost, 80.2% human agreement. Replaces rev2's Selective-k=3. |
| Runtime JIT research with ephemeral injection | Medium | Medium | P2.6 | Tier-1/2/3 source classification. |

Not adopted: Electron UI, PTY daemon, multi-account OAuth swap, Graphiti graph, Kanban, provider-abstraction.

## Prioritized Roadmap

### P0.0 — BUDGETS-Map Pre-Provisioning (blocker for all P0 subtasks) — NEW in rev4

`scripts/validate_token_budgets.py` enforces a 500-token default budget; any file exceeding this without a justified BUDGETS entry fails `make validate`. Before any P0.1–P0.6 merge:

- Extend BUDGETS map with entries for 7 expanded/new reference files + 14 KB-Artifact files. Each entry cites its plan item in a one-line rationale comment.
- Target budgets (Opus-4.7 tokenizer, ~35% above 4.6):
  - `agent-evaluation-guide.md` ≤1,800
  - `mcp-evaluation-guide.md` ≤1,200
  - `hook-evaluation-guide.md` ≤1,500
  - `report-parser-contract.md` ≤1,000
  - `task-type-rubric-variants.md` ≤1,500
  - `multi-source-merge-rules.md` ≤1,500
  - Each of 14 KB research files ≤3,000 (domain-appropriate justification)
- Optional extraction files pre-declared: `opus-4.7-migration-checks.md` ≤800, `mcp-2026-security-checklist.md` ≤800, `injection-regex-library.md` ≤700.

Pass criterion: `make token-budget` green on empty placeholders for all new files.

**rev4.2 — P0.0 execution decision (2026-04-19)**: `validate_token_budgets.py` scans only `skills/*/references/**/*.md`. Extending the scan to `research/` would surface ~25 existing files >2K tokens (e.g., `autonomous-agent-reliability.md` 7,531 tok, `tool-least-privilege-agents.md` 6,640 tok, `hook-based-runtime-observation-patterns.md` 6,092 tok) requiring per-file budget justification — out of P0.0 scope. **Resolution**: BUDGETS entries added only for files inside the current scan scope (7 reference files in `skills/*/references/`). The 14 KB-Artifact research files keep the "≤3,000 tok aspirational" target as a documented maintenance norm; enforcement deferred to a separate task. Two updated KB files already exceed 3,000 tok (skill-agent-format-conventions.md 4,119; hook-based-runtime-observation-patterns.md 6,092) — accepted because they encode dense official catalogs (15-field 2026 + 26-event CLI-pinned) where pruning would lose primary-source signal.

### P0 — Correctness Restoration (target: 4–5 weeks, parallelizable after P0.0)

**P0.1 — /review-agent: 15 frontmatter fields + Opus 4.7 tier + sampling-param migration**

- Update `research/claude-code/skill-agent-format-conventions.md` (authoritative Metadata source; not engineering-baseline).
- Patch `skills/review-agent/references/agent-evaluation-guide.md` covering the 7 missing fields (`maxTurns`, `effort`, `permissionMode` with 6 modes + parent-overrides-child hierarchy, `disallowedTools`, `skills`, `hooks`, `model` overrides including Opus 4.7).
- **SAMP-1 (PE-body check)**: skill/agent body contains no hardcoded `temperature`/`top_p`/`top_k` references (regex match). Grade: SAMP-1 FAIL → PE dimension capped at C.
- **SAMP-2 (Metadata frontmatter check)**: frontmatter override block free of removed sampling params. Grade: SAMP-2 FAIL → hard F on Metadata (runtime 400-error).
- If guide exceeds 1,800 Opus-4.7 tokens → extract Opus-4.7-breaking-checks into `skills/review-agent/references/opus-4.7-migration-checks.md` (loaded JIT when `model: opus-4-7` detected).
- Regenerate boundary-exemplars for the new fields.

Pass criterion: `/review-agent` on representative existing agent → zero Medium findings; all 15 fields surface in Current/Recommended where applicable; SAMP-1/2 detectable on crafted artifacts.

**P0.2 — /review-hook: 26-event catalog + version-min gating**

- New `scripts/verify_hook_events.py` (~50 lines): reads `claude --version`, looks up event-to-version from a repo-local map (simpler than rev2's changelog-scraper assumption — catalog is fully documented), outputs JSON whitelist. Unknown events → `status: unknown — verify against CLI version X.Y.Z`, not FAIL.
- Patch `hook-evaluation-guide.md`: cover all 26 events with version-min annotations; agent-type hook specifics (60s timeout, 50 tool-turns, Read/Grep/Glob only).

Pass criterion: `/review-hook hooks/hooks.json` zero Medium findings; per-event dimension grade emitted; unknown-event label applied where applicable.

**P0.3 — /review-mcp-server: MCP 2026 + April security disclosure + /scaffold-mcp-server (#25)**

- Rubric additions: lazy-loading adoption at >50 tools or >10K description tokens; `_meta["anthropic/maxResultSizeChars"]` annotation; elicitation mode correctness (form only for non-sensitive).
- **Two-tier prompt-injection scan** (PE-F8 fix):
  - Tier A (deterministic, primary): `skills/review-mcp-server/references/injection-regex-library.md` with ≥20 patterns: `"ignore (all )?(previous|prior) instructions"`, `/system:|###system/i`, base64-suspect blobs >200 chars, `[IMPORTANT]`/`[URGENT]` blocks, Unicode-tag chars (`\u{E0000}-\u{E007F}`).
  - Tier B (LLM, only on Tier-A hits): confirms severity and extracts context.
- April 2026 security checks: no hardcoded creds; OAuth Resource Server Metadata (RFC 9728); `.mcp.json` VCS-exclusion check when credentials detected.
- Scope-precedence awareness: local > project > user; duplicate-name detection.
- If guide exceeds 1,200 Opus-4.7 tokens → extract April-2026 checks into `mcp-2026-security-checklist.md`.
- Plus `/scaffold-mcp-server` (issue #25, scaffold half — `.mcp.json` declaration stub only per Q7).

Pass criterion: `/review-mcp-server .mcp.json` zero Medium findings; Tier-A regex library covers ≥20 injection patterns; `/scaffold-mcp-server test-server` produces valid fragment.

**P0.4 — /review-plugin (new) with injection-hardening**

- Scaffold via `/scaffold-skill plugin review-plugin`.
- Scope: `plugin.json` schema (3 required + 12 optional); top-5 failure-mode detection (components in `.claude-plugin/`, relative paths in URL marketplaces, version conflict, non-kebab-case skills, private repo without token); marketplace-compliance subset (reserved names, basic security); namespacing enforcement.
- **Injection hardening** (Agent-Harness-F5 fix): tool grants restricted to `Read, Grep, Glob`; `disallowedTools: [Bash, Write, Edit, WebFetch]` declared; IJ-4 regex scan on parsed manifest body for system-prompt syntax (`<system>`, `[INST]`, imperative verbs) → warning finding.
- Marketplace-submission-readiness out of scope (per Q2).
- Add to CLAUDE.md Command Inventory on completion.

Pass criterion: `/review-plugin .` on this repo → zero Medium findings; Command-Inventory entry present; injection hardening present in SKILL.md frontmatter.

**P0.5 — Rubric calibration, all items binary-verifiable (issues #4/#5/#6/#10)**

All checklist items use the canonical template (PE-F9):
```
<ID> <Short-Label>: <single observable in present tense>.
BOUNDARY PASS: <≤15-word example>.
BOUNDARY FAIL: <≤15-word example>.
Verification: <regex|glob|count|LLM-binary> <exact check>.
```

**#4 Trigger-consistency (Metadata B/C discriminator)** — 4 items (rev4 split from rev3's 3):
- **META-1a Trigger-Match-Primary**: `description.contains(body-primary-trigger-keyword)` regex. BOUNDARY PASS: "Use when reviewing MCP server configs" + body triggers on `.mcp.json`. BOUNDARY FAIL: body triggers on `.mcp.json` but description says "Use for configurations".
- **META-1b Trigger-Match-Generalization**: OR-joined with META-1a — description uses "when", "for", or domain term covering broader trigger.
- **META-2 Anti-Pattern Example**: description contains regex `/do ?not use|not for|skip (when|if)/i`. BOUNDARY PASS: "Do NOT use for agents or rules — use /review-agent instead." BOUNDARY FAIL: "Use this skill when you need to review a skill."
- **META-3a Concrete Trigger**: no description uses `/as needed|if appropriate|when useful/i`. BOUNDARY PASS: "when file contains hooks.json". BOUNDARY FAIL: "use as appropriate".
- **META-3b Sibling-Distinguishability**: no sibling SKILL.md in same plugin shares ≥2 trigger-keywords (token-set overlap).
- Grade boundary: META-1 ✗ → D/F (dispatch failure); META-2 ✗ → C; all ✓ → B; all ✓ + no sibling overlap → A.
- Evidence: arXiv:2602.16666 (R_prompt 61.8% drop on rephrasings); Anthropic blog 2026-01.

**#5 Observation masking parity (CE Grade-A)** — CE-X as binary check (PE-F2, CE-F9):
- **CE-X Compaction-Strategy Declaration**: If workflow keeps conversation history ≥10 turns AND uses LLM-based summarization, skill body contains ≥1 sentence citing why masking is insufficient. BOUNDARY PASS: "Rotating window: dropping entries older than 20 tool-calls" (masking declared). BOUNDARY PASS 2: "Summarize every 10 turns because semantic condensation required — masking would lose dependency-graph signal". BOUNDARY FAIL: "Summarize prior conversation every 10 turns via LLM call" without justification.
- Decision table in `engineering-baseline.md` §Observation Masking: (a) output <1K tokens AND turn-history ≤5 → neither required; (b) output ≥1K tokens AND non-decision-relevant → masking preferred; (c) output ≥1K tokens AND semantic condensation needed → summarization.
- Boundary-exemplar pair added to `skills/review-skill/references/boundary-exemplars.md`.
- Evidence: arXiv:2508.21433 (52% cost reduction, parity on SWE-bench Verified).

**#6 Verification criteria (Completeness A)** — COMP-X/Y/Z all binary:
- **COMP-X Success Criteria**: explicit success condition defined, not just output format. Verification: count of "complete when|success when|done when" patterns in skill body.
- **COMP-Y Verification Method**: programmatic check or explicit binary LLM item (not holistic "looks good"). Regex exclusion: `/looks good|seems correct|appears valid/i`.
- **COMP-Z Evidence Trail**: verification-decision evidence recorded. Regex: `/evidence|citation|quote|verified against/i` in output spec.
- Evidence: RubricEval (arXiv:2603.25133), RULERS (arXiv:2601.08654 QWK 0.73 vs 0.26), IFEval (arXiv:2311.07911 perfect κ), CheckEval (arXiv:2403.18771 +0.45), MAST FC3.

**#10 Task-type rubric variants (CE + GA)** — new doc file + resolution algorithm (PE-F4):
- Create `research/rubric-design/task-type-rubric-variants.md` with override tables (orchestrator, code-review, research-synthesis, scaffold, tutoring).
- **Task-Type resolution algorithm** (hybrid heuristic-first, reviewer-override):
  1. Deterministic heuristics (no LLM): `allowed-tools` contains `Write+Bash` → scaffold|orchestrator; name prefix `review-|audit-|classify-` → code-review; `research-|sync-|refresh-` → research-synthesis; `scaffold-|develop-|apply-` → scaffold; `allowed-tools` contains `Task` → orchestrator.
  2. Reviewer override: `/review-skill --task-type=<type>` CLI flag.
  3. Ambiguity (2+ heuristics match): LLM chooses with single-sentence justification; choice logged to report certificate.
- Link from `skills/review-claude-config/references/scoring-rubric.md`.
- Evidence: AdaRubric (arXiv:2603.21362, r=0.79 vs r=0.63 fixed).

**Baseline token-budget constraint** (CE-F3): post-refresh `engineering-baseline.md` ≤2,600 Opus-4.7 tokens. Current 2,575 after drift; adding items requires pruning equal-weight prose from existing sections — not appending. Enforced by `validate_token_budgets.py`.

**Batch all four issues into one baseline refresh via `/refresh-engineering-baseline`.**

Pass criterion: `/run-eval-cases all` passes; existing Medium findings do not regress; all new items detectable on crafted fixtures; baseline size ≤2,600 tokens; task-type-rubric-variants.md linked from scoring-rubric.md; boundary-exemplars.md updated.

**P0.6 — Known-critical-bug detectors with adversarial test cases**

- **#39523 detector** in `/audit-policy-compliance`: detect `defaultMode: "bypassPermissions"` + protected-dir write prompts; scan for PreToolUse hook `allow` returns followed by prompt.
- **#45551 detector** in new `/audit-mcp-auth`: macOS Team-plan session multiplicity >5; `claudeAiOauth` entry age anomalies; keychain JSON size >2010 bytes truncation risk.
- **Adversarial robustness** (Agent-Harness-F6): detectors normalize input before regex match (lowercase, trim, Unicode NFC). Pass criterion expanded: ≥5 adversarial test cases per rule (whitespace, case, Unicode, comment-obfuscation, split-value) must be caught.

Pass criterion: crafted test cases trigger detectors; adversarial set caught; false-positive rate ≤10% on real audit runs in this repo.

**Baseline-serialization rule** (all P0):
- `engineering-baseline.md` edited only by P0.5 via `/refresh-engineering-baseline`, exactly once, after P0.1–P0.4 + P0.6 land.
- P0.1–P0.4, P0.6 write only to type-specific guides, `skill-agent-format-conventions.md`, or new per-skill reference files.

**Parallelization matrix:**
- P0.0 strictly first.
- P0.1 ‖ P0.2 ‖ P0.3 ‖ P0.4 ‖ P0.6 parallel.
- P0.5 strictly last.

**P0-exit verification hook** (Agent-Harness-F9): run `/validate-primitive-dependencies .` after **each** P0-subtask merge AND once after P0.5. Zero orphan references, zero broken skill→file links. Blocks P0-completion until clean.

### P1 — Architectural Gap Closure (target: 4–6 weeks after P0)

**P1.1 — Multi-perspective reviewer with Trust-or-Escalate + full harness spec**

Resolves Agent-Harness-F1 through F4 and F10 through F12:

- **Subagent definition location**: perspectives defined as top-level agents under `agents/review-perspective-{clarity,correctness,integration}.md` (Agent-Harness-F1). Rationale: perspectives are dispatch-driven delegation targets for `TaskCreate`, not description-matched skills. Creates new `agents/` directory in this repo.
- **Frontmatter matrix per perspective** (Agent-Harness-F2, F3, F4, F11):

| Perspective | `model` default | `tools` | `disallowedTools` | `maxTurns` | `isolation` | `permissionMode` |
|---|---|---|---|---|---|---|
| A Clarity | `haiku-4-5` | Read, Grep, Glob | Write, Edit, Bash, mcp__*, TaskCreate, TaskUpdate, TaskGet, TaskList, WebFetch, WebSearch | 20 | none | dontAsk |
| B Correctness | `haiku-4-5` | Read, Grep, Glob, Bash | Write, Edit, mcp__*, TaskCreate, TaskUpdate, TaskGet, TaskList, WebFetch, WebSearch | 30 | worktree | dontAsk |
| C Integration | `haiku-4-5` | Read, Grep, Glob, WebSearch | Write, Edit, Bash, mcp__*, TaskCreate, TaskUpdate, TaskGet, TaskList, WebFetch | 25 | none | dontAsk |

Rationale: Haiku default preserves Trust-or-Escalate 1.35× cost model; explicit `Task*` denial prevents sub-sub-agent spawn (trust-chain bounding); `isolation: worktree` for Correctness because Bash writes could mutate state; `dontAsk` for all because read-only reviews. On escalation (see trigger below), orchestrator overrides `model: opus-4-7` per-perspective via `TaskCreate` parameter.

> **[2026-04-20 AMENDMENT — P1.1 pilot implementation deviation]** The escalation model on the landed pilot is **flag-only by default** (not auto-upgrade). ESC-1/2/3/4 set `escalation_required: true` on the merged certificate with `reasons: [...]`; the user re-invokes `/review-skill --deep <path>` manually for Opus-tier escalation. **Auto-re-run is restricted to ESC-5** (degraded mode — any perspective returned null/malformed certificate). Also: `permissionMode: default` replaces `dontAsk` (documented Anthropic semantics; disallowedTools hard-deny holds in all modes); Correctness `Bash` grant and worktree isolation dropped (no documented use-case; attention-scope principle). Agent + Task* explicitly added to each perspective's `disallowedTools`, plus `mcpServers: []` belt-and-suspenders. Rationale: eliminates orchestrator Tier-A1/A2 triads (no Bash+WebFetch+Write co-occurrence); restores tools-hierarchy byte-identity across Clarity + Correctness (Integration keeps WebSearch, 1-tool delta accepted). See `skills/review-skill/references/perspective-dispatch-protocol.md` and `merge-rules.md` for authoritative merge/escalation specification. Auto-upgrade pattern can be restored in P1.1b once `--deep` user behavior is measured.
- **Tool-least-privilege 5-tier combo check** (Agent-Harness-F3): Correctness (Bash) without WebSearch avoids Tier-A1; Integration (WebSearch) without Bash avoids Tier-A1; combined they would be Tier-A1 so never granted to same perspective.

- **Shared prefix** (CE-F1, CE-F2): byte-identical rubric + engineering-baseline + source-quality-criteria. Measured 2026-04-19: 1,930 + 2,575 + 415 + 300-token wrapper ≈ 5,220 Opus-4.7 tokens. Target 4,500–5,500, hard floor 4,200 to preserve cache qualification. Per-perspective suffix budget ≤800 tokens (focus directive + 2–3 boundary exemplars). Total per sub-agent call: 5.2K prefix + artifact (≤4K) + suffix (≤800) ≈ 10K tokens baseline.

- **Escalation execution order** (CE-F8): first perspective runs **synchronously** to prime shared-prefix cache; perspectives 2 and 3 run in parallel after first-token return confirms cache write. Cost model: 1× P1 + 2 × 0.15× P2/P3 ≈ 1.3× baseline (matches Trust-or-Escalate 1.35× target).

- **Invocation strategy — Trust-or-Escalate binary thresholds** (PE-F7):
  - ESC-1: |weighted_score − grade_boundary| ≤ 2.5 points (numeric proximity).
  - ESC-2: finding severity set contains High AND Low without any Medium (mixed U-shape).
  - ESC-3: max(perspective_scores) − min(perspective_scores) ≥ 2 letters (A=95, B=85 arithmetic).
  - ESC-4: explicit `--deep` flag.
  - Any of {ESC-1, ESC-2, ESC-3, ESC-4} triggers escalation. All decidable by non-LLM script.

- **Domain ownership explicit in each sub-agent prompt** (PE-F6). Each perspective system prompt ends with:
  ```
  You own these checklist items: [list].
  If you detect a finding outside your ownership:
    - Record it with severity=Low, flag owner_conflict=true, note "cross-domain signal for <owner>".
    - Do NOT grade the affected dimension.
  The orchestrator aggregates cross-domain signals for the owner to validate.
  ```
  Ownership assignments:
  - **Clarity** owns: WS-*, RD-5, PD-1 (readability, structure).
  - **Correctness** owns: COMP-X/Y/Z, CE-X, SAMP-*, RD-4, RD-6 (factual, robustness).
  - **Integration** owns: IJ-*, SP-*, META-* (dependency, lifecycle, safety-of-chain).
  Non-overlap table documented in `research/finding-identity/multi-source-merge-rules.md`.

- **Merge rules** (PE-F5, CE-F10, PE-F6):
  - **Layer 0 — content-dedup** (runs first): if two findings share (path, line-range, ≥80% token-overlap on evidence quote), merge into one finding multi-tagged with `dimensions={A,B,...}`.
  - **Layer 1 — domain ownership tie-break**: Safety→B, Clarity→A, Integration/Dependencies→C.
  - **Layer 2 — weighted vote by confidence**.
  - **Layer 3 — lexicographic deterministic breaker**.
  - **Layer 4 — escalate to manual-review** if conflicting high-confidence votes remain.
  - **Dual-layer fingerprint**: Layer-1 exact-merge via SARIF `partialFingerprints` (path + dimension + line-hash); Layer-2 flag-for-review via (path + dimension) without line — soft-merge via embedding similarity ≥0.92, flag-for-manual at ≥0.85, never embedding alone.
  - **Boundary-exemplars shared** across all 3 perspectives (BARS evidence: 30% → <5% rater divergence). Revisit only if variance exceeds convergence tolerance post-pilot.

- Pilot `/review-skill` first; port to `/review-agent`, `/review-rule`, `/review-hook` only after convergence holds (two consecutive runs on unchanged files: same finding-id set at Impact High/Medium, ≤1-letter grade variance, no null dimensions).

- **Delegation-tracker matcher updates** (Agent-Harness-F8): `hooks/delegation_tracker.py` matcher extended for the 3 new custom agent types (`review-perspective-clarity`/`-correctness`/`-integration`). `/review-hook hooks/hooks.json` run for convergence.

- **Delegation-tracker log-rotation** (Agent-Harness-F10): log size >10 MB per session → rotate to `.1`-suffix. Added to risks; monitoring suggested.

- Shared-prefix pattern documented in `docs/skills/README.md` (≤300 words, §Multi-Perspective Review Pattern; links to full spec in `research/agent-knowledge-caching/aperant-orchestration-patterns.md`).

Pass criterion: convergence holds on 3 representative artifacts; shared-prefix ≥4,200 tokens; Trust-or-Escalate cost multiplier ≤1.5× on eval-cases fixture; all 4 review skills ported; delegation traces show all 3 perspectives in audit log.

**P1.2 — 3-tier structured-output recovery with full grant/timeout/logging contract**

New shared reference `skills/review-claude-config/references/report-parser-contract.md`:
- Tier 1: strict parse.
- Tier 2: LLM-assisted extraction with minimal 7-field schema (summary_items, total_findings, high_impact_count, medium_impact_count, recommendations_text, validation_warnings, confidence_score).
- Tier 3: regex-based text fallback (verdict keywords, section parsing, finding-id extraction).

**Full contract** (Agent-Harness-F7):
- **Pre-condition**: all 5 `apply-*` skills get `TaskCreate, TaskGet, TaskUpdate` added to `allowed-tools`. Verification: `/validate-primitive-dependencies` green before merge.
- **Tier-2 timeout contract**: `maxTurns: 5`, hard timeout 90s. On timeout → Tier-3 regex fallback.
- **Trust-chain visibility**: `delegation_tracker.py` matcher extended for `TaskCreated`/`TaskCompleted` events (F3 Hook-Catalog v2.1.84), reconstructable chain `apply-* → repair-structured-output → Task-Response` in `$CLAUDE_PLUGIN_DATA/audit/`.

Update 5 apply-* skills to reference contract. New skill `skills/repair-structured-output/` with model invocation enabled for Tier-2.

Pass criterion: malformed-report fixture recovered via Tier 2 without session crash; delegation-tracker shows full chain; `/validate-primitive-dependencies` green on the 5 updated apply-* skills.

### P2 — Research, Workflow & Housekeeping (quarterly cadence)

**P2.0 — CLAUDE.md consolidation** (CE-F7, new in rev4)

Current CLAUDE.md is 252 lines; research §Research References is 32 entries adding 14 would reach 46 entries ≈ 3,300 Opus-4.7 tokens in §Research alone, pushing total over 8,500 tokens and violating 200-line rule-application optimum (research/agent-knowledge-caching: 92% <200 lines vs 71% >400).

Action: extract §Research References to `docs/research-index.md`; replace in CLAUDE.md with a 5-line pointer. Preserves JIT-loading trigger phrases. Enforce `wc -l CLAUDE.md ≤200` in `make validate`.

**P2.1** Research backlog (#28–#33, #41, #43–#46).
**P2.2** Workflow chains (#22 eval-cases D1–D10, #23 hook-chain, #24 CLAUDE.md chain, #26 auto-re-review).
**P2.3** Auto-memory awareness in `/audit-memory-hygiene` (F5): 200-line-head convention, 3 poisoning vector detectors.
**P2.4** Cache-status labels — 4-state schema with transitions; `/check-repo-health` surfaces STALE.
**P2.5** Docs-page gaps (validate-deps v2 report). Per-file decision: create docs vs. remove link for repo-internal. Batch-scope multi-perspective review, not per-file. Add `docs/skills/review-plugin.md` in same batch after P0.4.
**P2.6** Runtime JIT research fallback — Tier-1/2/3 sources, ephemeral injection, no disk persistence.
**P2.7** Atomic report writes — write-to-tmp + rename + retry wrapper.
**P2.8** IDEAS.md design decisions.

### P3 — Speculative / Low ROI / Blocked

- #39 CI/CD PR review — blocked (API key policy).
- Low-priority issues (#34–#37, #42, #47–#57, #60) — dedicated grooming session.
- F6 `/ultrareview` — no programmatic API trigger; at most emit text recommendation in review reports (Q4).
- F7 Monitor — defer until #50258 + #45976 resolved.
- F11 plugin git-index leak — niche; park.
- Provider-abstraction (Aperant) — skipped.

## Error Findings & Corrections from Deep Research + Plan Review

- rev2's "46% coverage gain" refined to 45%→94% with multi-model ensemble (arXiv:2512.16272); PoLL κ 0.627–0.841 → 0.763–0.906.
- rev2's perspective triad (Risk/Convention/Dependency) was correct for code review; wrong for skill/agent/rule. Corrected to Clarity/Correctness/Integration.
- rev2's /ultrareview cost ($5–20) wrong; actual $15–25. No programmatic API trigger exists.
- rev2's `verify_hook_events.py` over-scoped; the 26-event catalog is documented, so tool is a map lookup not a scraper.
- rev2's Selective-k=3 (1.6×) replaced by Trust-or-Escalate (1.35× with 80.2% human agreement).
- 6 broken Quick-Reference docs-page links confirmed (validate-deps v2 report) → P2.5.
- Untracked git files (IDEAS.md, PROGRESS.md, .mcp.json, .claude/reviews/, 50+ Plans/*.md) — per-file commit/gitignore decision should precede P0.
- Stale 2026-04-04 suggest-skills report — regenerate after P0.5.
- MCP April 2026 security disclosure → P0.3 first-class rubric item.
- Two critical 9-month-old bugs (#39523, #45551) → P0.6.
- rev3 omitted: subagent definition location, frontmatter matrix, tool-grants matrix, sampling-param migration, binary-verifiable rubric items, explicit domain-ownership prompts, adversarial test cases for detectors, Tier-A regex library for injection scan, BUDGETS-map pre-provisioning, CLAUDE.md bloat, sequential-first escalation, dual-layer fingerprint, apply-* TaskCreate grants, delegation-tracker matcher updates, `/validate-primitive-dependencies` as P0/P1 exit, self-referential verification. **All added in rev4.**

## Mid-Session Rubric-Freeze Rule (new in rev4; to land in CLAUDE.md as part of P0.5)

**Rule**: rubric and `engineering-baseline.md` changes are committed between sessions, never mid-session. Mid-session baseline/rubric modification invalidates the shared prefix used by all perspective sub-agents and violates KV-cache friendliness. If a critical rubric bug is found mid-session, abort the session, fix via `/refresh-engineering-baseline` in a fresh session, then re-run. Expected cache-hit degradation of mid-session changes: 84% → <20%.

This rule goes into CLAUDE.md §Working Guidelines as part of P0.5's baseline refresh, not as a deferred item.

## Open Questions

- **Q1**: Fixed 3-perspective set vs. primitive-specific? Default: fixed (Clarity/Correctness/Integration).
- **Q2**: P0.4 marketplace-submission-readiness in scope? Default: local-plugin-correctness only.
- **Q3**: F3 hook events — current CLI version exposing full 26-event catalog? `verify_hook_events.py` returns `unknown` for above-version events.
- **Q4**: F6 `/ultrareview` integration — emit local recommendation in review reports, or stay silent?
- **Q5**: After P1.1, single-perspective default vs. always-3? Default: Trust-or-Escalate with `--deep` opt-in.
- **Q6**: Shared vs. per-perspective boundary exemplars? Default: shared (BARS).
- **Q7**: `/scaffold-mcp-server` scope — `.mcp.json` declaration stub only, not full server codegen.
- **Q8**: P0.6 detector false-positive tolerance — 10% default, tune after first audit.

## Critical Files

**P0 files touched:**
- `scripts/validate_token_budgets.py` (P0.0 BUDGETS extension)
- `research/claude-code/skill-agent-format-conventions.md` (P0.1)
- `skills/review-agent/references/agent-evaluation-guide.md` (P0.1); optional extraction `opus-4.7-migration-checks.md`
- `skills/review-agent/references/boundary-exemplars.md` (P0.1, P0.5)
- `scripts/verify_hook_events.py` (new, P0.2)
- `skills/review-hook/references/hook-evaluation-guide.md` (P0.2)
- `skills/review-mcp-server/references/mcp-evaluation-guide.md` (P0.3); optional extractions `mcp-2026-security-checklist.md`, `injection-regex-library.md`
- `skills/scaffold-mcp-server/` (new, P0.3)
- `skills/review-plugin/` (new, P0.4)
- `CLAUDE.md` (P0.4 Command Inventory entry; P0.5 rubric-freeze rule)
- `skills/review-claude-config/references/scoring-rubric.md` (P0.5)
- `research/rubric-design/task-type-rubric-variants.md` (new, P0.5)
- `skills/review-claude-config/references/engineering-baseline.md` (P0.5 only)
- `skills/audit-policy-compliance/references/detection-rules.md` (P0.6)
- `skills/audit-mcp-auth/` (new, P0.6)

**P1 files touched:**
- `agents/review-perspective-{clarity,correctness,integration}.md` (new, P1.1)
- `skills/review-skill/` + orchestrator refactor (P1.1 pilot)
- `skills/review-agent/`, `skills/review-rule/`, `skills/review-hook/` (P1.1 port)
- `docs/skills/README.md` (P1.1 shared-prefix doc)
- `hooks/delegation_tracker.py` (P1.1 custom agent matchers; P1.2 Task events)
- `research/finding-identity/multi-source-merge-rules.md` (new, P1.1)
- `skills/review-claude-config/references/report-parser-contract.md` (new, P1.2)
- `skills/repair-structured-output/` (new, P1.2)
- `skills/apply-*/SKILL.md` (P1.2, 5 files: TaskCreate grants)

**P2 files touched (selection):**
- `CLAUDE.md` (P2.0 extract §Research References)
- `docs/research-index.md` (new, P2.0)

## Verification

Per-phase verification uses repo's validation stack:
- After any rubric/baseline change → `/review-*` on representative artifact + `/run-eval-cases`.
- After any cross-primitive reference change → `/validate-primitive-dependencies`.
- After any code change → `make validate`.
- After P1.1 pilot → convergence criterion.
- Before any commit → zero Medium findings on change artifact.

**Exit criteria** (rev4 explicit):
- **P0 exits** when: P0.0 BUDGETS green; P0.1–P0.4 + P0.6 parallel tracks Medium-zero reports; P0.5 baseline refresh complete (size ≤2,600 tokens); `/run-eval-cases all` passes; `/validate-primitive-dependencies` green after each subtask AND after P0.5.
- **P1 exits** when: P1.1 convergence on 3 pilot artifacts + 4 review skills ported + shared-prefix doc merged + perspectives appear in delegation-tracker; P1.2 malformed-fixture recovered + all 5 apply-* skills reference contract + trust-chain visible in audit logs; `/validate-primitive-dependencies` green.
- **Self-referential verification** (Agent-Harness-F12): at P1-exit, run `/review-skill skills/review-skill/SKILL.md` once in single-perspective mode and once with `--deep`; zero Medium findings. Analogously for `/review-agent` on `review-agent` SKILL.md (non-perspective mode). Strongest dogfooding available.

## Risks & Mitigations

- **Tier-2 source over-trust on F3/F4/F11** — mitigated by version-pinning + `unknown` labels + P0.2 CLI-version-lookup tool.
- **Multi-perspective cost** — Trust-or-Escalate (1.35×, 80.2% agreement) + shared-prefix caching; `--deep` opt-in for critical reviews.
- **Baseline churn** — serialization rule: only P0.5 writes `engineering-baseline.md`; exactly once; after other P0 items.
- **`engineering-baseline.md` concurrency** — no parallel `/refresh-engineering-baseline` across sessions.
- **P0.4 underestimation** — new skill creation is the largest P0 item; budget ~1.5 weeks standalone; split P0.4a (schema+basic) vs P0.4b (marketplace-compliance to P2) if schedule pressure.
- **Opus 4.7 breaking changes** — existing agents using `temperature`/`top_p`/`top_k` will 400-error. P0.1 SAMP-1/2 items catch this.
- **Prompt-cache churn on Opus 4.7 new tokenizer** — ~35% more tokens means cached prefixes may miss 4,096 minimum. P0.5 baseline refresh right-sizes to ≤2,600 tokens total, keeping combined prefix (5,220) above hard floor (4,200).
- **Delegation-tracker log flooding** (Agent-Harness-F10) — 5–10× volume with Trust-or-Escalate; rotation at >10 MB/session + monitoring recommended.
- **Hidden dependencies**:
  - P1.1 requires P0.5 complete (perspectives run against calibrated rubric).
  - P1.1 sub-agents consume rubric refinements from P0.5 (META-1a/1b/2/3a/3b, CE-X, COMP-X/Y/Z, SAMP-1/2) — must land in order.
  - P2.5 requires P0.4 complete.
  - P0.6 detectors reference bug IDs that may close upstream; re-verify issue state before each release.
- **Plan-mode re-entry** — once P0 starts, do not re-enter plan mode; extend this file.

## KB Artifacts Appendix — Files to Write/Update on Plan Approval

**Naming convention** (corrected in rev4.1 per maintainer feedback): research files use domain-specific names without year/quarter suffixes. Time-sensitive information lives in YAML frontmatter (`last_refreshed: YYYY-MM-DD`) and inline version notes within the file (e.g., "Added 2026-04-16 (CLI v2.1.111): Opus 4.7 `xhigh` effort"). On refresh, existing sections are edited in place — obsolete material removed, new material added — so the research index grows only when genuinely new domains appear, not every calendar cycle.

**Action split**: of the 14 deep-research payloads, **5 update existing domain files in place** (append new sections with inline version markers, bump `last_refreshed`), and **9 create new domain-specific files** (all named without year suffix). Net new entries in CLAUDE.md §Research References: 9, not 14.

### UPDATE (5 existing domain files):

| # | Path | Action | Source agent |
|---|------|--------|--------------|
| U1 | `research/claude-code/skill-agent-format-conventions.md` | append §"Agent frontmatter 2026 catalog" with 15 fields + Opus 4.7 tier + SAMP-1/2 migration notes; bump `last_refreshed` | F2 + F8 |
| U2 | `research/hook-observation/hook-based-runtime-observation-patterns.md` | append §"Event catalog (CLI-version-pinned)" with all 26 events, runtime-type table, agent-hook specifics | F3 |
| U3 | `research/mcp-server-quality/mcp-server-configuration-quality.md` | append §"Protocol updates" (tool-search/lazy-loading, elicitation, `_meta` annotations, `.mcp.json` new fields) and §"Security disclosure (disclosed 2026-04-16)" with mitigations | F4 |
| U4 | `research/change-discipline/change-discipline-workflow-research.md` | append §"Multi-perspective review patterns" with corrected effectiveness metrics (45%→94%), Trust-or-Escalate cost model, perspective-set rationale for skill/agent/rule review | Multi-perspective |
| U5 | `research/finding-identity/finding-identity-and-lifecycle.md` | append §"Multi-source merge rules" with dual-layer fingerprint, tie-break algorithm, shared boundary-exemplars spec | Finding identity |

### NEW (9 domain-specific files, no year in filename):

| # | Path | Source agent |
|---|------|--------------|
| N1 | `research/claude-code/plugin-system.md` | F1 |
| N2 | `research/claude-code/auto-memory-system.md` | F5 |
| N3 | `research/claude-code/ultrareview-service.md` | F6 |
| N4 | `research/claude-code/monitor-tool.md` | F7 |
| N5 | `research/claude-code/known-issues.md` (quarterly sections inline, e.g. §"2026-Q1", §"2026-Q2"; new sections appended, stale entries removed) | Known-issues |
| N6 | `research/fix-completeness/structured-output-recovery-patterns.md` | 3-tier recovery |
| N7 | `research/agent-knowledge-caching/aperant-orchestration-patterns.md` | Aperant orchestration |
| N8 | `research/agent-knowledge-caching/cache-labels-and-jit-research.md` | Aperant orchestration |
| N9 | `research/rubric-design/rubric-calibration-evidence.md` | Rubric calibration |

Plus companion (P0.5 item #10): `research/rubric-design/task-type-rubric-variants.md`.

### Refresh workflow (applies to both UPDATE and NEW files)

On next refresh cycle (e.g., Opus 4.8 release or MCP spec revision):
- Edit the domain file in place; do not create `<name>-<year>.md` spin-offs.
- Update `last_refreshed` in frontmatter.
- Within the body, use inline version markers where specifics matter: "Added 2026-04-16 (CLI v2.1.111): …", "Superseded 2026-Q3 by …", "Deprecated 2026-10: …".
- Remove material that is genuinely obsolete (not just older).
- Rename files only when the underlying domain fundamentally splits or merges — never for calendar reasons.

After UPDATE/NEW writes: CLAUDE.md §Research References gains exactly **9 new entries** (not 14) — OR extracted to `docs/research-index.md` (if P2.0 done first). `/validate-primitive-dependencies` must confirm no orphans. Updated files keep existing index entries; descriptions revised only if domain scope changed.
