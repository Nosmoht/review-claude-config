# Evidence-Backed Refactor Roadmap for `review-claude-config`

This document tracks what is already complete and what remains after the evidence-layer, runtime-contract, and baseline-guidance cleanup work. It is a roadmap and supporting analysis artifact, not a canonical contract.

## Summary

The foundational scientific-hardening work has been implemented. This roadmap remains a supporting planning artifact only. The remaining work is bounded release validation on the current candidate tree, operational maintenance of the evidence layer, and later documentation-trimming so canonical contracts stay authoritative.

## Completed Foundations

### 1. Canonical evidence layer

- `evidence-contract.md` is now the canonical vocabulary for repo-level claim classes.
- `engineering-baseline.md` and the baseline refresh path use explicit evidence classes.
- Maintainer guidance points to the canonical evidence layer instead of inventing alternate labels.

### 2. Canonical review/report contract

- `review-report-contract.md` is now the forward-looking authority for review/report structure.
- Review, apply, analytics, and health-check surfaces were aligned to that contract in Wave 3.

### 3. Baseline and maintainer-guidance alignment

- `refresh-engineering-baseline`, `CLAUDE.md`, and related guidance now agree on the three baseline sections.
- Shared source filtering and claim classification are separated more cleanly.

### 4. Documentation authority trim

- User entrypoint, maintainer guide, and system-map docs were trimmed to reduce duplicated contract prose.
- The scaffold workflow now targets the surviving doc authorities instead of the removed redundant sections.

## Remaining Work

### 1. Finish bounded release validation on the candidate tree

- Use validation-only bounded modes for the longest maintenance and review surfaces so final release gating can complete deterministically.
- Keep release claims conservative until the exact post-fix candidate passes that validation matrix.

### 2. Operate the evidence-layer maintenance process

- Keep dossier-style evidence artifacts maintained under the process defined in [`evidence-maintenance.md`](evidence-maintenance.md).
- Keep cited local `research/*` summaries annotated with provenance metadata only, while leaving repo-level interpretation in the dossier.

### 3. Trim documentation drift further

- Update `README.md`, `CLAUDE.md`, and `docs/skills/*` to explain workflow and rationale while pointing at canonical contracts instead of restating prompt logic.
- Keep `docs/review-eval-cases.md` as a behavior regression harness, not as a second normative source of truth.

### 4. Audit-Followup Roadmap Items (added 2026-05-02)

External academic-style review (on file with maintainer, dated 2026-05-02) flagged two items as enhancements rather than gaps. Both are tracked here, not as discrete issues, because they require ongoing or pilot work rather than bounded delivery.

#### 4a. Runtime SKILL.md Trim Sweep

The audit recommends moving long protocols from `SKILL.md` files into `references/` to honor Progressive Disclosure. The existing `scripts/validate_token_budgets.py` already enforces per-file budgets; a systematic sweep would validate that each runtime SKILL.md serves only the *minimal* workflow with details deferred to references. Open questions: which skills are over budget today, is the budget itself well-calibrated, do consumers actually traverse to references when needed.

Recommended approach: add a `/audit-skill-bloat` skill that ranks all SKILL.md files by token-budget headroom + reference-density ratio; pilot on the lowest-headroom skill before sweeping. Defer until at least one reviewer report flags excessive SKILL.md token cost as a finding.

#### 4b. Pilot Ablation Study

The audit recommends ablation studies for: multi-agent vs single, with/without binary evaluator, with/without domain cache, with/without hooks, reduced rubric, weaker model, with/without apply automation. The full matrix is AI-time expensive (multiple full reviews per ablation). Realistic pilot: pick the highest-uncertainty design choice (multi-perspective vs single-judge — partially explored in the existing isolated-judge-per-dimension scoring work) and run a controlled before/after on 5 eval cases. If the pilot shows meaningful signal, expand to additional ablations one at a time.

Recommended approach: integrate ablation tracking into `/run-eval-cases` as an opt-in `--ablation <component>` flag rather than building a separate harness. Defer until either the multi-perspective scoring change ships or a stakeholder asks for ablation evidence.

## Test Plan

- **Evidence integrity**
  - Strong repo-level claims in shared references and top-level docs map to Tier 1 evidence or an explicit repo-default / low-evidence label.
- **Documentation alignment**
  - Top-level docs and skill docs point to the canonical evidence and review/report contracts without competing with them.

## Non-Goals

- No new Python runtime or evaluation engine.
- No replacement of the current skill-based architecture with a code-heavy framework.
- No removal of research-driven features solely because their evidence is weaker; the change is to label and scope them correctly.

## Success Criteria

- A future maintainer can tell, for any major repo rule, whether it is science-backed, vendor-guided, a repo default, or a low-evidence area.
- The strongest claims remain defensible from primary sources.
- The weakest-evidence features remain usable, but are clearly framed as heuristic or policy-driven.
