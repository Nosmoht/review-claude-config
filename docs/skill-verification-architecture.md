# Skill Verification Architecture — Per-Output-Class Form Mapping

Date: 2026-05-26
Status: Accepted (supersedes the initial 5-template architecture from `.work/skill-verification/` Phase 2 outputs)

## Context

In May 2026 we applied a uniform 3-layer verification pipeline (Layer A mechanical / Layer B adversarial blind-critic / Layer C 6-dim binary rubric) to all 37 local skills in this repo, modeled on `~/.claude/skills/reword-skill/SKILL.md`. The pipeline was implemented across 5 output-class templates (REVIEW / AUDIT / APPLY / SCAFFOLD / MAINTAIN) in `.work/skill-verification/<class>-template.md`.

A retrospective deep-research dispatch surfaced that the uniform application was a **right-altitude violation** (per `~/workspace/claude-config/rules/right-altitude.md`): the 3-layer pipeline was originally designed for text-rewrite information-preservation verification (a judgment-shaped failure mode), and generalizing it to deterministic / mechanically-verifiable output classes adds token cost and false-positive surface without raising assurance.

This document records the corrected per-output-class verification form mapping and the lessons learned.

## Per-output-class form mapping

| Output class | Skill count | Verification form | Rationale |
|---|---|---|---|
| **REVIEW** | 11 | **3-layer (A+B+C)** — keep all | Reviewer-style LLM output is the canonical LLM-as-judge target; documented TPR > 96% / TNR < 25% asymmetry (`skills/review-claude-config/references/review-discipline-evidence.md`) justifies Layer B cross-persona dispatch. CheckEval-style binary rubric (Layer C) decomposes judgment per arXiv:2403.18771. |
| **AUDIT** | 9 | **3-layer with Layer-B-gate** | Audit output is structured extraction when predicates are mechanical (file exists / regex matches / exit code). Layer B fires ONLY when ≥X% of predicates are LLM-judged rather than mechanically-decided. Pure-mechanical audits: Layer A + Layer C sufficient. |
| **APPLY** | 5 | **Layer A + AST-diff + mutation-survival** | Adversarial-critic on a diff is wrong-shape. The right Tier-1 primitives are deterministic: RefDiff (arXiv:1704.01544, precision 100% / recall 88% on refactoring detection), property-based mutation testing (arXiv:2301.13615), PGS framework (FSE 2025, +37.3% correctness gain). Layer B as currently implemented is replaced by structural assertions. |
| **SCAFFOLD** | 5 | **Layer A only (`make validate` + idempotency hash)** | Output class is structurally-constrained generation. `make validate` exit-0 is sufficient as the verification primitive. Adversarial-critic asks "is this a good skill?" — but the scaffolder's contract is "did you produce a syntactically valid skill matching the template," not "is this a high-quality skill" (which is `/review-skill`'s job, run separately). Quality assessment belongs in REVIEW, not SCAFFOLD. |
| **MAINTAIN** | 7 | **Layer A only (schema + idempotency hash + freshness predicate)** | Verification predicates are deterministic: `f(f(x)) == f(x)` for idempotency, timestamp-vs-policy-bound for freshness, closed-set transition table for state-machine validity. Snapshot testing (Verify framework, Jest pattern) is the textbook fit. No judgment surface = no Layer B. |

## Per-skill mapping

The 5-class assignment of the 37 local skills lives in `.work/skill-verification/categorization.md` (gitignored working artifact). For clarity:

- **REVIEW (11)**: review-claude-config, review-skill, review-agent, review-rule, review-hook, review-mcp-server, review-plugin, review-settings, review-claude-md, review-domain-currency, review-analytics
- **AUDIT (9)**: audit-context-budget, audit-mcp-auth, audit-memory-hygiene, audit-policy-compliance, audit-repo, audit-trust-chain, classify-trace-errors, review-session-trace, suggest-skills
- **APPLY (5)**: apply-review-findings, apply-skill-review-findings, apply-agent-review-findings, apply-rule-review-findings, apply-audit-findings
- **SCAFFOLD (5)**: scaffold-skill, scaffold-agent, scaffold-rule, scaffold-mcp-server, develop-hooks
- **MAINTAIN (7)**: check-repo-health, refresh-evidence-coverage, run-eval-cases, validate-primitive-dependencies, `.claude/skills/maintain-evidence-layer`, `.claude/skills/refresh-engineering-baseline`, `.claude/skills/sync-research-index`

The categorization is by **output shape** (judgment-shaped vs deterministic), NOT by CLAUDE.md command-organization grouping. Four skills classified non-intuitively: `review-analytics` is REVIEW (trend-analysis output is judgment-shaped); `classify-trace-errors`, `review-session-trace`, `suggest-skills` are AUDIT (predicate+classification output).

## Tier-1 evidence anchors

Researcher dispatch (2026-05-26, deep mode) surfaced:

- **From Prompts to Properties: PBT for LLM Code Generation** (FSE 2025, ACM DL 10.1145/3696630.3728702) — primary verification primitive for LLM-generated code; PGS framework reports +37.3% correctness vs conventional verification. Direct relevance to APPLY class.
- **RefDiff: Detecting Refactorings in Version Histories** (arXiv:1704.01544) — precision 100%, recall 88% on refactoring detection. Tier-1 primitive for APPLY-class diff verification (structural assertions, not narrative critique).
- **Property-Based Mutation Testing** (arXiv:2301.13615) — mutation testing as deterministic alternative to LLM-judge for "does the patch fix what it claims".
- **A Survey on LLM-as-a-Judge** (arXiv:2411.15594, v6) — catalogues judge calibration via IRT, confusion-matrix correction, sensitivity/specificity bounds. Required reading before deciding Layer B fires.
- **Chrysalis: Metamorphic Testing in Python** (ASE 2025 Tool Demo) — metamorphic-testing framework for code-model verification.
- **Meta Automated Compliance Hardening (ACH)** — production deployment using mutation testing to guide LLM-based code changes; mutation-survival as deployed verification primitive at industrial scale.

CheckEval / G-Eval / IFEval / FollowBench citations carried over from the original `reword-skill` design remain valid for REVIEW class but were over-applied to non-judgment-shaped classes.

### URL provenance

Per `~/workspace/claude-config/rules/web-research.md §URL provenance`:

- **Researcher-resolved (2026-05-26 dispatch, validated per `agents/researcher.md §4`):** RefDiff, Property-Based Mutation, LLM-as-Judge Survey, PGS / FSE 2025, Chrysalis ASE 2025, Meta ACH.
- **Orchestrator-re-verified (2026-05-26 same session):** RefDiff (arXiv:1704.01544 — confirmed paper title, authors, 100%/88% precision/recall), Property-Based Mutation (arXiv:2301.13615 — confirmed Bartocci et al. 2023), LLM-as-Judge Survey (arXiv:2411.15594 — confirmed Gu et al. 2024).
- **Paywall-gated, researcher-verified-only:** PGS / FSE 2025 (ACM DOI 10.1145/3696630.3728702 — orchestrator WebFetch returned HTTP 403; cite text only, not URL, in downstream skill bodies).

## Lessons learned

1. **Pre-research before pattern generalization** — `rules/capability-claims.md` requires a literature check before claiming "X is the right approach for output class Y." We claimed the 3-layer pipeline was right for all 5 output classes without literature-checking whether the failure forms in each class were judgment-shaped. 10 minutes of deep research at design time would have saved 2-3 hours of implementation + retrofit.
2. **Right-altitude test per output class explicitly documented BEFORE implementation** — Phase 3 user-review of the 5 templates asked "approve all 5 templates" without explicitly surfacing "for each class, is the failure form judgment-shaped or deterministic?" A per-class altitude-check table at Phase 3 would have caught SCAFFOLD/MAINTAIN as overkill.
3. **Sub-agent challenge before approval** — A team-red dispatch on the 5 templates before Phase 4 implementation would likely have surfaced the SCAFFOLD/MAINTAIN over-engineering. Adversarial subagent dispatch (~5 minutes wallclock) is cheap relative to implementation cost (~2 hours wallclock for 17 over-engineered skills).
4. **Clear separation: VERIFICATION (was the output produced correctly) vs. QUALITY (is the output good)** — The scaffold-skill case is canonical: verification belongs in the scaffolder (did `make validate` pass?), quality belongs in `/review-skill` (is this a good skill?). Conflating them collapses the right-altitude ladder.

## Implementation status

- 2026-05-25: initial 3-layer pipeline implemented across all 37 skills (commits `547f6ab..df628ac`).
- 2026-05-26: retrofit per this document. Categories:
  - REVIEW: no change (correct as implemented).
  - AUDIT: Layer B gated by predicate-density check.
  - APPLY: Layer B replaced by AST-diff + mutation-survival primitives.
  - SCAFFOLD: Layer B + Layer C dropped; Layer A retained (`make validate` + idempotency).
  - MAINTAIN: Layer B + Layer C dropped; Layer A retained (schema + idempotency + freshness).

## Out of scope for this document

- Specific Layer A script bodies per skill — those live in each `SKILL.md`'s `## Quality measurement` section.
- The original 5 category-templates under `.work/skill-verification/` — historical artifacts, no longer authoritative.
- Future retrofit of any specific skill's verification section — fix-as-needed via the usual `/apply-skill-review-findings` flow.
