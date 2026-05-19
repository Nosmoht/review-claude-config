# Evidence-Backed Gap Analysis for `review-claude-config`

This document evaluates the current repository against [`scientific-research-dossier.md`](scientific-research-dossier.md) after the completed evidence-layer, review-contract, and baseline-guidance cleanup work.

## Summary

The repository is now structurally much stronger than the earlier transitional state. The biggest remaining issues are no longer missing contracts, and heuristic honesty is no longer the primary unresolved block. The main remaining issues are **sustaining the evidence-layer maintenance process in practice**, **documentation duplication that can reintroduce drift**, and **finishing bounded release validation on the current candidate tree**.

## Current Strengths

### 1. The canonical evidence layer now exists

- [`evidence-contract.md`](../skills/review-claude-config/references/evidence-contract.md) defines the only canonical repo-wide claim classes.
- [`engineering-baseline.md`](../skills/review-claude-config/references/engineering-baseline.md) and the baseline refresh path now use that vocabulary explicitly.

### 2. The review/report contract is centralized

- [`review-report-contract.md`](../skills/review-claude-config/references/review-report-contract.md) is now the canonical report structure for new review outputs.
- Review, apply, analytics, and health-check surfaces have already been aligned to that authority.

### 3. Prompt/context-first architecture remains evidence-backed

- The repo still treats context engineering, explicit contracts, and tool clarity as core quality concerns.
- This remains aligned with current Anthropic and related agent literature.

### 4. Source-quality filtering and maintainer guidance are now better separated

- `source-quality-criteria.md` governs filtering and cross-validation for research inputs.
- `evidence-contract.md` governs how repo claims are labeled after evidence is evaluated.

## Remaining High-Priority Gaps

### 1. The wider evidence layer now has a process, but it still depends on manual follow-through

Problem:
- `evidence-maintenance.md` now defines cadence, triggers, and precedence for the wider evidence layer, but the process is still manual and can be skipped.

Why it matters:
- The repo can still drift scientifically at the evidence-doc layer if maintainers stop running the defined review cycle.

Required change:
- Keep the manual review cycle active and consider future health-check support only if manual drift becomes a recurring problem.

### 2. Final release validation still needs bounded operational proof

Problem:
- The repository now has stronger contracts and documentation, but the longest noninteractive maintenance flows still need a bounded validation path so release gating can complete deterministically.

Why it matters:
- Without a bounded validation path, the repo can claim more release confidence than the final operational gate has actually demonstrated.

Required change:
- Keep release claims conservative until the candidate passes the bounded validation matrix on the exact post-fix tree.

## Medium-Priority Gaps

### 3. Documentation remains too repetitive

Problem:
- `README.md`, `CLAUDE.md`, and `docs/skills/*` still restate significant process logic.

Why it matters:
- Even with canonical contracts, duplicated prose remains the easiest way for drift to return.

Required change:
- Shift docs further toward contract explanation, rationale, and navigation rather than repeated prompt prose.

### 4. Local research summaries now have bounded provenance, but coverage stays intentionally narrow

Problem:
- Only the currently cited `research/*` artifacts carry provenance metadata. The rest of the research tree remains outside that maintenance surface.

Why it matters:
- This keeps the maintenance burden bounded, but future dossier expansion requires disciplined promotion of additional summaries into the citation set.

Required change:
- Add provenance metadata only when a local research summary becomes part of the dossier citation set, and keep repo-level claim classes out of those files.

## Lower-Priority Gaps

### 5. Analytics policy could still be reframed more clearly as local design

- Path-first identity is already treated more honestly than before, but future docs should continue to present it as repo policy rather than scientific necessity.

### 6. Repo audit and suggestion systems still need continued maintenance discipline

- `audit-repo` and `suggest-skills` now surface uncertainty more explicitly, but their heuristic rules still need periodic evidence review as the repo evolves.

## Maintenance Actions

- Follow the evidence-layer maintenance process in [`evidence-maintenance.md`](evidence-maintenance.md) for cadence, triggers, and precedence.
- Keep contradictions canonical in [`scientific-research-dossier.md`](scientific-research-dossier.md) while keeping local `research/*` files metadata-only.
- Expand provenance annotations to additional local research summaries only when they are promoted into the dossier citation set.
- Reduce duplicated prose in `README.md`, `CLAUDE.md`, and `docs/skills/*`.
- Keep canonical contracts authoritative and make the docs point to them rather than restating them.

## Acceptance Criteria

- No major low-evidence subsystem is described as if it were settled science.
- Evidence artifacts above the baseline have a clear maintenance story.
- Canonical contracts remain the source of truth; supporting docs explain them without competing with them.
