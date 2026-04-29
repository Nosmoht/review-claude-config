# Plan: #98 — Description-Collision under Skill Contention

## Context

Issue #98 closes the largest evidence gap in the **Metadata** dimension per `docs/dimension-evidence-coverage.md` (Metadata = 2nd-largest gap with 5/6 items as Repo-defaults, only one Anthropic-blog source). With 32 skills under `skills/*/SKILL.md`, many sharing verbs (`review-*` × 9, `audit-*` × 5, `apply-*` × 4), description-collision is a real routing risk.

**Current state** (Phase 1 exploration):
- `scoring-rubric.md` §"Trigger-Consistency" L101-110 defines META-1a / 1b / 2 / 3a / 3b / 4. Only META-4 cites a Tier-2 source; the other five are Repo-defaults.
- META-3b sibling-distinguishability is regex-implemented in `scripts/rubric_binary_evaluator.py` L533-664: `find_sibling_skills` globs `skills/*/SKILL.md` (already plugin-wide), `tokenize_description` filters stopwords, overlap `>= 2 shared tokens` → FAIL unless `has_sibling_counter_reference` regex matches **on either side** (L548 — `own_fm` OR `sib_fm`).
- The `review-skill` ↔ `review-agent` pair currently PASSES because `review-claude-config`'s counter-reference rescues them via the bilateral-OR semantics.
- Token budget headroom: `scoring-rubric.md` ~4,900 / 9,800 (50% remaining).

**Question**: Does Tier-1 published research justify a new Metadata rubric item or refinement of META-3b, or is the gap a documented null result?

## Phase A — Web Research (preceded by preflight)

**Preflight (read-only, before searches)**:
1. Read `scripts/rubric_binary_evaluator.py` and capture verbatim:
   - `META_3B_COUNTER_REFERENCE` regex constant (exact source line + pattern)
   - `STOPWORDS` set
   - Current overlap threshold (currently `>= 2` per Phase 1; verify)
   - `find_sibling_skills` glob scope (currently plugin-wide per Phase 1)
2. Read `skills/review-claude-config/references/evidence-contract.md` to confirm label semantics ([Proven result] / [Engineering guidance] / [Repo default]).
3. Run a **baseline verdict-snapshot script** (Phase C-prep, ad-hoc): import `find_sibling_skills`, `tokenize_description`, `has_sibling_counter_reference` as a library; record per-skill META-3b PASS/FAIL/NA verdicts to `Plans/98-baseline-verdicts.txt`. **No threshold change is committed before this snapshot exists.**

**Search execution** per `~/.claude/workspace/claude-config/rules/web-research.md` (≥2 query formulations per sub-query, **3 sub-queries × ≥2 formulations = ≥6 queries minimum**, max 3 cycles):

1. **Tool-selection accuracy under contention** — Gorilla (Patil et al. arXiv:2305.15334), ToolBench (Qin 2023), MetaTool, ToolLLM. Look for: routing accuracy degradation curves vs description-overlap; embedding-vs-token-similarity primitives.
2. **Mixture-of-experts gate quality** — Switch Transformers, Hash Layers, expert-routing under load. Look for: principled disambiguation criteria.
3. **Anthropic-specific routing semantics** — recent Anthropic Engineering blog + Claude Code docs on multi-skill plugin discovery. Look for: official skill-activation primitive (embedding similarity? exact match? LLM-judge?).

**Tools**: WebSearch first (low cost), Jina Reader (`https://r.jina.ai/<url>`) for top 1-2 results per sub-query. **Source-quality filter**: peer-reviewed / arXiv / Anthropic-DeepMind-OpenAI-authored ≥50 citations OR ≤18 months old.

## Phase B — Decision Tree

After Phase A:

**Path 1 — Tier-1 evidence found (≥2 sources)**:

Operationalization preference order (revised — additive before mutative):

- **(1b PREFERRED) Add a new META-3c item** with the cited evidence-cited threshold. Additive change: existing META-3b stays untouched; META-3c addresses the cross-cutting collision angle the literature surfaces (e.g., embedding-distance, intent-coverage). Lower regression risk; reversible.
  - **Naming**: `META-3c` extends the META-3 family per repo convention (matches META-1a/1b, META-3a/3b precedent). Not META-5, not META-DC.
  - **Atomic 4-touch-point update** (mandatory, all four together):
    1. `scoring-rubric.md` §"Trigger-Consistency" — add META-3c with iff-predicate, sources, PASS/FAIL examples
    2. `skills/review-skill/references/skill-evaluation-guide.md` — add table row IF the item is digit-suffix-style and regex-detectable; SKIP IF letter-suffix-only narrative item (matches GA-X / COMP-V convention)
    3. `scripts/rubric_binary_evaluator.py` `NON_BINARY_ITEMS` — add `META-3c`
    4. `tests/test_rubric_binary_evaluator.py` — verify guide-coverage test still passes (no fixture changes if META-3c is letter-suffix-style)

- **(1a FALLBACK) Refine META-3b threshold/scope** only if literature shows META-3b is *fundamentally wrong-direction* (e.g., embedding similarity is the right primitive). Mutative change: high regression risk to existing PASS-verdicts.
  - **Mandatory regression gate**: pre-change baseline-verdicts snapshot from Phase A preflight. Reject any threshold change that flips >2 skills without explicit per-skill review and migration plan.
  - **Domain-stopword extension required**: current `STOPWORDS` does not strip `skill|agent|rule|claude|config|plugin|review|audit` — these dominate overlap sets when scope is cross-skill. Adding them is part of the change.
  - Test fixtures at `tests/test_rubric_binary_evaluator.py` L267-286, L858, L889, L920, L972-980 lock current behavior; ≥6 assertions need re-baselining; new fixture SKILL.md files may be required.

**Path 2 — Null result (no Tier-1 sources)**:
1. Write `research/agent-skills/description-disambiguation.md` documenting the null result + dated search trail (queries tried, sources rejected, why). Negative results are the deliverable.
2. **Recommendation block**: e.g., "Wait for Anthropic to publish skill-routing semantics" / "Run our own empirical test if cross-skill mis-routing is observed". Label any META-3b heuristic as `[Repo default]`.
3. **CLAUDE.md research-reference entry is MANDATORY in Path 2** (not optional) — otherwise `/validate-primitive-dependencies` flags the new file as an orphan.
4. **No rubric change.** No baseline change. No evaluator change.

**Special-case fallback (literature contradicts existing META-3b)**: if Phase A surfaces evidence that token-overlap is the *wrong-direction* primitive (e.g., embedding similarity dominates), pre-commit that META-3b stays in place under Path 2 *labeled `[Repo default, contradicted by literature]`*, and a follow-up issue is filed for a clean-slate redesign — never silently keep a refuted heuristic.

## Phase C — Self-Application Audit (both paths, mandatory)

**Method**: write `scripts/audit_description_collision.py` (one-off audit script, not committed unless useful as a recurring tool):
1. Imports `find_sibling_skills`, `tokenize_description`, `has_sibling_counter_reference`, `META_3B_COUNTER_REFERENCE`, `STOPWORDS` from `rubric_binary_evaluator.py` as a library.
2. Globs `skills/*/SKILL.md`.
3. Computes pairwise Jaccard similarity on stopword-filtered description tokens.
4. Reports pairs with similarity > 0.3 (heuristic threshold, document this).
5. For each high-overlap pair, flags whether a counter-reference exists.

**Likely outcome**: review-* / audit-* / apply-* families surface as high-overlap clusters. Each is rescued by counter-reference if present. Skills lacking counter-reference are real META-3b violations and trigger a follow-up issue.

**Output table** in the new research file: pair, similarity, counter-ref status, verdict.

## Phase D — Documentation & Token Budget

**Both paths**:
- New research file `research/agent-skills/description-disambiguation.md` with `name:` + `description:` + `last_refreshed: 2026-04-29` frontmatter.
- CLAUDE.md research-references entry under "Agent Skills & Quality" section (L226), exact format:
  ```
  - [Description Disambiguation Under Contention](research/agent-skills/description-disambiguation.md) — <one-line summary with key sources or null-result note>. Load when reviewing Metadata dimension META-3* items or auditing skill-description collisions.
  ```

**Path 1 only**:
- Token budget: only bump `scoring-rubric.md` if the addition pushes over 9,800. Current headroom is ~4,900 — most likely no bump needed. If bump needed, update both `scripts/validate_token_budgets.py` AND `tests/test_validate_token_budgets.py`.
- **Do NOT touch `engineering-baseline.md`** — CLAUDE.md L156 restricts baseline scope to "Prompt Engineering, Context Engineering, and Tool Design". Metadata techniques live in `scoring-rubric.md` or in the new research file, NOT in baseline.

**Evidence-label assignment**:
- Path 1, refined META-3b or new META-3c with cited Tier-1 sources → `[Proven result]`
- Path 1, item synthesized from heuristics with partial literature backing → `[Engineering guidance]`
- Path 2 (null result) — any META heuristic that remains is `[Repo default]`

## Critical Files

| File | Change | Notes |
|---|---|---|
| `research/agent-skills/description-disambiguation.md` | Create (both paths) | `last_refreshed: 2026-04-29` frontmatter required |
| `scoring-rubric.md` § Trigger-Consistency | Edit (Path 1 only) | Add META-3c (preferred) or refine META-3b (fallback) |
| `scripts/rubric_binary_evaluator.py` | Edit (Path 1 only) | NON_BINARY_ITEMS extension; if Path 1a, also threshold + STOPWORDS extension |
| `tests/test_rubric_binary_evaluator.py` | Edit (Path 1a only) | Re-baseline ≥6 assertions; possibly new fixture SKILL.md files |
| `skills/review-skill/references/skill-evaluation-guide.md` | Edit (Path 1, only if regex-style new item) | Match digit-suffix vs letter-suffix convention to placement decision |
| `CLAUDE.md` | Edit (both paths) | Research References under "Agent Skills & Quality" |
| `scripts/validate_token_budgets.py` + `tests/test_validate_token_budgets.py` | Edit (Path 1 only, only if rubric exceeds 9,800) | ~50% headroom currently |

**Reusable existing infrastructure** (must be imported, not duplicated):
- `scripts/rubric_binary_evaluator.py` — `find_sibling_skills`, `tokenize_description`, `has_sibling_counter_reference`, `META_3B_COUNTER_REFERENCE`, `STOPWORDS`
- All importable as library (module-level pure functions, no `__main__`-side effects)

## Verification

End-to-end checks before commit:
1. Phase A preflight verbatim regex/threshold/STOPWORDS values captured in plan-execution notes (not assumed).
2. Phase A baseline verdict-snapshot exists (`Plans/98-baseline-verdicts.txt`) — required even on Path 2 for trail.
3. Web-research-rule compliance: ≥6 queries executed (≥2 formulations × 3 sub-queries), ≥2 Tier-1 sources cited (Path 1) OR documented null result with full search trail (Path 2).
4. Phase C self-application table populated in the new research file (both paths).
5. `make validate` — all 812 tests pass; no token-budget violations.
6. Path 1a only: post-change verdict diff shows ≤2 flipped verdicts vs baseline OR explicit per-skill review for each flip.
7. CLAUDE.md research-reference entry present in BOTH paths; `/validate-primitive-dependencies` would not flag an orphan.
8. Evidence label assigned to any new technique per `evidence-contract.md`.

## Adversarial-Review Findings Integrated

This revision integrates findings from three perspective reviews:

- **Risk/Regression**: pre-change verdict-snapshot is mandatory; domain-stopword extension required for any cross-skill scope change; embedding-similarity contradiction has explicit fallback.
- **Convention**: META-3c (not META-5/META-DC) per repo family convention; `last_refreshed:` frontmatter and CLAUDE.md entry format both made explicit; evidence labels specified per path.
- **Dependency**: 4-touch-point chain made atomic; CLAUDE.md update mandatory in both paths (not optional); Path 1b preferred over Path 1a (additive vs mutative); engineering-baseline.md edit dropped per CLAUDE.md L156 scope rule.

## Out of Scope

Per issue:
- Building a new disambiguation eval framework
- A/B testing skills under simulated contention
- Refactoring existing skill descriptions to comply with a stricter rubric (separate follow-up issues per real violation surfaced in Phase C)
