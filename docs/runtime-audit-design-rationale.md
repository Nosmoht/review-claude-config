# Runtime Audit Design Rationale

Scope decisions made during Phase 1-5 implementation (2026-04-14). Records why specific deliverables were built, merged, simplified, deferred, or skipped. Prevents future re-exploration of already-decided questions.

## Phase 2b — Policy Engine

**`/audit-escalation-correctness` → MERGE into `/audit-policy-compliance`.**
The existing skill already does basic escalation analysis (L4 calls with prior AskUserQuestion check). Deep chain tracking, gap detection, and subagent escalation flags are incremental depth on the same analysis axis. A separate skill would duplicate trace parsing infrastructure. The merged Step 7 adds full L4 chain tracking without a new skill.

## Phase 3 — Dynamic Security

**`/probe-injection-resistance` → SIMPLIFY to IJ-* checklist items.**
80% of injection surface analysis overlaps with existing Safety checklist items (SP-2, SP-4, TV-2, TV-3) that already evaluate tool grants and high-risk combinations. The genuine gap — cross-primitive data flow analysis (external input → privileged action without boundary) — is addressed by IJ-1/IJ-2 checklist items plus the `injection-surface-catalog.md` reference. No separate skill needed because single-file reviews already check these patterns, and the `/review-claude-config` orchestrator covers cross-file batch analysis.

**`/audit-trust-chain` → DEFER from Phase 3, then BUILD in Phase 4 with post-hoc enrichment.**
Initially deferred because audit traces lack declared tool grants per agent (`tools:` field). The Phase 4 design found a workaround: parse CLAUDE.md at each delegation event's CWD to extract agent configs post-hoc. This is fragile (CLAUDE.md may have changed since the session) but provides useful signal with graceful degradation when config is unavailable.

**Containment architecture spec → SKIP.**
No consuming skill exists. Research papers without consumers go stale. The `action-classification.md` reference and `hook-observation-patterns.md` research already document the plugin's containment capabilities. Defer the spec to when an MCP server build actually begins.

**MCP tool classification → PATTERN-BASED, not blanket L4.**
`hooks/policy_gate.py` originally treated every `mcp__*` tool as L4 (`Act` → ask). This conflated reads (`list_*`/`get_*`/`retrieve_*`/`search_*` and `_read` suffix) with mutations (13 verb prefixes plus `_write` suffix). Pattern dispatch in `_classify_mcp_tool` keeps the conservative L4 default for unknown suffixes while letting opt-in `policy.json` users skip prompts on read-only ops. The skill reference `audit-policy-compliance/references/action-classification.md` is updated in lockstep so static audit and the live hook agree.

## Phase 4 — Autonomous Governance

**Goal-drift detection → SKIP (partially).**
Detecting goal drift from traces requires inferring user intent from prompts and comparing against tool-call sequences. Without labeled baseline data (task → expected tool distribution), detection is unreliable. Tool-sequence anomaly detection is theoretically possible but needs training data the repo doesn't have. Deferred to when sufficient trace data accumulates.

**Containment architecture spec → SKIP (repeated).**
Both Phase 3 and Phase 4 considered this. Same rationale: premature without a consuming skill. The architectural boundaries table in CLAUDE.md documents what requires external infrastructure.

## Phase 5 — Meta-Audit

**`/meta-evaluate` → NO NEW SKILL, extend existing.**
`/run-eval-cases` already owns the pattern of synthetic artifact + acceptance criteria + PASS/FAIL verdict. FP/FN measurement is a natural extension (match finding_ids against defect arrays). `/review-analytics` already owns trend tracking. Convergence analysis (View 4) extends its existing time-series infrastructure. Building a separate `/meta-evaluate` skill would duplicate both.

**Recursive loop safety checker → SKIP.**
The system doesn't have recursive review loops. The convergence requirement in CLAUDE.md already prevents infinite review-apply cycles by requiring two consecutive stable runs. No additional tool needed.

## Explicitly Deferred Deliverables

These were in the original roadmap but deferred with documented rationale:

| Deliverable | Phase | Why Deferred |
|---|---|---|
| `/run-behavioral-benchmarks` | 2a | Needs labeled training data (task → expected tool distribution). No baseline data exists yet. |
| Reproducibility runner (N runs + variance) | 2a | Requires CI pipeline invoking Claude Code programmatically. Outside plugin model. |
| Decision Authority Model reference | 2b | Action classification model (L1-L5) covers the core. Formal authority model is governance-theoretical without a consuming enforcement mechanism. |
| `/review-escalation-policy` skill | 2b | Escalation rules are plain-markdown rules reviewable via `/review-rule`. EP-1/EP-2 checklist items handle the quality checks. Dedicated skill not justified. |
| Goal-drift detection | 4 | Requires intent inference from prompts + tool-sequence anomaly baselines. Partially theoretical without labeled data. |
| Recursive loop safety checker | 5 | CLAUDE.md convergence requirement + bounded review-apply cycle already prevents infinite loops. No additional tool needed. |

## General Principles Established

1. **Extend before creating.** When an existing skill covers 60%+ of a proposed skill's scope, extend it rather than creating a new skill.
2. **Post-hoc enrichment over hook enhancement.** When trace data is incomplete, prefer parsing static configs at trace CWDs over modifying hooks — hooks change the data collection surface and require separate testing.
3. **Opt-in for enforcement, always-on for observation.** Observation hooks (audit_logger, delegation_tracker) are always active. Policy enforcement (policy_gate) is opt-in via policy.json — zero impact on sessions without explicit policy configuration.
4. **Research before implementation.** Every phase that involved novel design started with research (QW-5 hook observation, injection taxonomy, memory poisoning patterns) before building skills.
5. **Review with the repo's own harness.** Every artifact was reviewed via `/review-skill`, `/review-hook`, or `/review-claude-md` before commit. Plan agents are supplementary, not primary quality gates.
