---
name: isolated-judge-spike
description: Methodology + 5-skill selection rationale for issue #137 isolated-judge-per-dimension scoring spike. Empirical runs deferred.
last_refreshed: 2026-05-28
parent_issue: 137
parent_proposal: 67
status: methodology-delivered-empirical-pending
---

# Isolated-Judge-Per-Dimension Scoring Spike — Methodology + Plan

**Scope of this document**: Phase 1 deliverable of issue #137. Documents methodology, 5-skill selection rationale, measurement schema, and decision framework that will guide the empirical runs (AC-2 + AC-3 + AC-4) when those execute. Empirical runs themselves are tracked separately as a follow-up issue (spillover per Phase 7.6).

## Why this spike exists

Issue #67 proposes migrating `/review-skill` from single-pass scoring of all 7 dimensions to **isolated-judge-per-dimension**: each dimension scored by a separate subagent call.

**Tier 1 evidence** supporting the convergence win:

- Anthropic (2026) — *Demystifying Evals for AI Agents*: per-criterion isolated judging reduces evaluator-as-judge correlation bias (TPR>96%/TNR<25% in cross-criterion contamination per arXiv:2510.11822).
- Prometheus 2 (EMNLP 2024, arXiv:2405.01535): direct-assessment vs pairwise-ranking has different bias profiles; isolated-criterion direct-assessment dominates pairwise on factuality-style dimensions.
- Repo-internal `research/llm-evaluator-consistency/llm-evaluator-consistency.md`: ICC3 improvement +46% with behavioral anchoring; k=3 majority-vote reduces variance.

**Cost / risk concerns** that block direct migration:

- 7× judge calls per skill is the headline number; **actual token cost depends on shared-prefix cache hit rate** which is unknown for the 7-call shape.
- The existing multi-perspective dispatch already depends on 84% KV-cache hit rate (per CLAUDE.md §Working Guidelines). A 7-call shape that fragments the prefix could break that.
- No R4-bounded cost cap in #67. The spike collects empirical data so #67 can re-scope with a real cost cap.

## Methodology

### AC-1: 5-skill selection — rationale

Selection drawn from existing skills in this repo. Spanning Grade A→D coverage required by AC; observed grades from historical `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` data are the historical anchor.

| # | Skill | Predicted-grade band | Rationale |
|---|---|---|---|
| 1 | `review-skill` | A (large, mature) | Highest-complexity skill in the repo; most binary items in scope; tests narrative-scoring path |
| 2 | `audit-repo` | A-B | Multi-phase orchestrator skill with subagent dispatches; tests cross-tool grant evaluation |
| 3 | `apply-skill-review-findings` | B+ | Apply-class skill with confirmation gates; tests Safety dimension surface |
| 4 | `scaffold-rule` | B | Smaller scaffold; tests rule-specific dimension subset (Clarity/Completeness/GA only) |
| 5 | `audit-memory-hygiene` | B-C (newer, less polish) | Borderline-band coverage; tests Goal-Alignment + Metadata under tighter activation criteria |

This 5-skill set covers (a) all 4 task-type variants per rubric L223–230 (orchestrator, code-review, scaffold, general-purpose), (b) grade-band spread A→C, and (c) sizes spanning ~250 lines to ~1500+ lines so per-skill token-input cost varies meaningfully.

### AC-2 / AC-3: Measurement schema (per skill × per mode × 3 runs)

For each (skill, mode, run-index ∈ {1, 2, 3}) tuple, record:

| Field | Source | Notes |
|---|---|---|
| `input_tokens` | Anthropic API response `usage.input_tokens` | Per-call sum across all subagents in the dispatch |
| `cache_read_input_tokens` | Anthropic API response `usage.cache_read_input_tokens` | The 90%-discount tier |
| `cache_creation_input_tokens` | Anthropic API response `usage.cache_creation_input_tokens` | The write-tier; 5-min TTL by default |
| `output_tokens` | Anthropic API response `usage.output_tokens` | — |
| `dim_grades` | Parsed from cert frontmatter | 7-vector: Clarity, Completeness, PE, CE, GA, Safety, Metadata |
| `total_cost_usd` | Derived | input × $3/MTok + cache_read × $0.30/MTok + cache_creation × $3.75/MTok + output × $15/MTok (Opus 4.7 cents/MTok) |
| `wallclock_seconds` | Orchestrator timestamp | — |

### AC-3 prototype design (`/review-skill --isolated-judge`)

Sketch (to be implemented in spillover issue):

1. Add `--isolated-judge` argument to `skills/review-skill/SKILL.md`.
2. When the flag is present, replace the single multi-perspective dispatch with **7 parallel subagent calls**, one per dimension. Each subagent gets:
   - the SKILL.md content + frontmatter
   - the dimension-specific rubric clause from `scoring-rubric.md` §<dimension>
   - the dimension-specific binary items from §Item Inventory
   - explicit prompt: "Score ONLY <dimension>. Do not consider other dimensions."
3. Aggregate the 7 returns into the same cert format the single-pass mode emits.
4. Cache strategy: all 7 calls share an identical prefix (the SKILL.md + rubric body); only the dimension-clause differs in the tail. Prefix-cache hit rate should approach 90%+ after the first call writes the cache.

### AC-4: Computing deltas

For each (skill, dimension):
- **ΔConvergence**: `variance(single_pass_grades_3runs) - variance(isolated_grades_3runs)`. Positive = isolated converges better; negative = isolated diverges more.
- **ΔCost**: `mean(isolated_total_cost_usd) - mean(single_pass_total_cost_usd)`. Per-skill marginal cost.
- **Cache hit rate**: `cache_read_input_tokens / (input_tokens + cache_read_input_tokens)`, computed per mode.

## Recommendation derivation framework (AC-5)

Decision rules (to apply after empirical data lands):

1. If **ΔConvergence positive AND ΔCost ≤ 2× single-pass mean**: recommend migration with cost cap = ⌈2× current mean⌉.
2. If **ΔConvergence positive AND ΔCost > 2× single-pass mean**: recommend selective migration — only for high-stakes-structural diffs.
3. If **ΔConvergence negative OR not significantly different**: do not migrate; document the failed hypothesis in #67.
4. If **cache hit rate <70% in isolated mode**: flag prefix-fragmentation risk in #67; consider Trust-or-Escalate (per `research/selective-multi-rating/`) as alternative.

### AC-6: #67 update

A summary comment on #67 will be posted referencing this file + the empirical follow-up issue.

## What this document does NOT yet contain (empirical work)

- AC-2 actual `/review-skill` single-pass runs (5 skills × 3 = 15 runs)
- AC-3 actual prototype implementation + runs (5 × 3 = 15 runs)
- AC-4 computed delta tables
- AC-5 final recommendation (do / do-not / selective migrate)

These are deferred to a spillover follow-up issue per Phase 7.6 discipline. The empirical runs require ~30 LLM-orchestrated `/review-skill` dispatches plus prototype implementation, which exceeds remaining session-context budget. Resume protocol: open spillover issue, dispatch in fresh session.

## Identified prefix-cache risks (a priori, before empirical)

Per CLAUDE.md §Working Guidelines:
> Mid-session rubric/baseline freeze. `scoring-rubric.md` and `engineering-baseline.md` are committed BETWEEN sessions, never edited mid-session. Mid-session changes invalidate the shared prefix used by perspective sub-agents and break KV-cache friendliness (84% → <20% cache-hit drop).

The 7-dimension fanout shape adds a NEW prefix-fragmentation surface: even with no rubric edits, the 7 calls each load **a different dimension-clause as the dispatching prompt's tail**. The shared prefix is the SKILL.md + the rubric BODY; the tail differs per call. Anthropic's prompt-cache implementation matches **prefix to first-divergence-point**, so:

- If dimension-clauses are embedded **as the final ~200 tokens** of the prompt and the rest is shared: cache hit rate is excellent.
- If the dispatching skill interleaves dimension-clause into the middle of the prompt (e.g., "Focus on <dimension>" appears before the rubric body): cache breaks at that point.

**Prototype implementation must enforce dimension-clause-as-tail** to maximize cache effectiveness. This is a design constraint the empirical phase must respect; otherwise the cost numbers are not representative.

## References

- Issue #137 (this spike), Issue #67 (parent proposal)
- Anthropic (2026) — Demystifying Evals for AI Agents (Tier 1)
- Prometheus 2 — arXiv:2405.01535 (Tier 1, EMNLP 2024)
- arXiv:2510.11822 — LLM-judge sycophancy + agreeableness (Tier 1)
- `research/llm-evaluator-consistency/llm-evaluator-consistency.md` (repo, Tier 1)
- `research/selective-multi-rating/` (repo, Trust-or-Escalate pattern)
- `skills/review-claude-config/references/scoring-rubric.md` §Item Inventory
- `CLAUDE.md §Working Guidelines` (KV-cache invariant)
