# Evidence Maintenance Guide

This guide tells maintainers how to classify claims in `review-claude-config` without overstating certainty.

## Use the Canonical Contract

Repository-level evidence classification is defined in [`evidence-contract.md`](/home/nos-ai/workspace/review-claude-config/skills/review-claude-config/references/evidence-contract.md).

Use only these classes:

- `Proven result`
- `Engineering guidance`
- `Repo default`
- `Low-evidence area`

Do not introduce alternate labels in top-level docs or shared references.

## How to Classify a Claim

### Proven result

Use when the claim is directly supported by Tier 1 evidence.

Examples in this repo:

- Domain knowledge can materially improve agent quality.
- Focused context management matters for agent performance.

### Engineering guidance

Use when official guidance or credible technical literature supports the pattern, but the result is not a strong universal benchmark claim.

Examples in this repo:

- Use minimal tool sets and explicit tool descriptions.
- Use Claude Code hooks for lightweight guidance and session checks.

### Repo default

Use when the repository chooses a convention or threshold for operational reasons.

Examples in this repo:

- Path-first identity in review analytics.
- Repo-specific token budgets or refresh workflows when they are not directly benchmark-backed.

### Low-evidence area

Use when the subsystem is useful but direct literature is thin or mostly heuristic.

Examples in this repo:

- Skill-gap detection as a general method.
- Primitive derivation from repository signals into Claude Code primitives.

## Mapping Older Wording

| Old wording | Replace with |
|---|---|
| Local design preference | Repo default |
| local policy | Repo default |
| heuristic / novel contribution / limited evidence | Low-evidence area |

## Maintainer Rules

- If a stronger source contradicts a local summary, update the local wording and record the contradiction rather than hiding it.
- If a claim cannot be defended with Tier 1 or strong Tier 2 evidence, do not present it as settled fact.
- If a rule is primarily chosen for this repo’s workflow, label it `Repo default`.
- When in doubt between `Engineering guidance` and `Repo default`, use `Repo default` unless the guidance clearly comes from an authoritative external source.

## Dossier and Research Lifecycle

Use this section as the single maintenance-process authority for the wider evidence layer.

### Cadence

- Review `docs/scientific-research-dossier.md`, `docs/repo-gap-analysis.md`, and `docs/evidence-backed-refactor-plan.md` every 90 days.
- Use the same 90-day rhythm as the repo's baseline freshness discipline, but keep this process manual.

### Triggers

Run an evidence-layer maintenance pass when any of these happen:

- the scheduled 90-day review comes due
- `docs/scientific-research-dossier.md` is edited
- a source cited in the dossier is added or replaced
- a stronger source contradicts a cited local summary

### Ownership and Precedence

- Evidence-layer upkeep is manual maintainer work, not skill ownership.
- `refresh-engineering-baseline` remains limited to `engineering-baseline.md`.
- Local `research/*` provenance annotations are source metadata only.
- Repo-level interpretation lives in [`evidence-contract.md`](/home/nos-ai/workspace/review-claude-config/skills/review-claude-config/references/evidence-contract.md) and [`scientific-research-dossier.md`](/home/nos-ai/workspace/review-claude-config/docs/scientific-research-dossier.md).
- Record contradictions canonically in `docs/scientific-research-dossier.md`, not in local research summaries.

### Normalization Checks

- Use only the canonical class names from `evidence-contract.md` for repo-level claims.
- Treat [`evidence-contract.md`](/home/nos-ai/workspace/review-claude-config/skills/review-claude-config/references/evidence-contract.md) and [`review-report-contract.md`](/home/nos-ai/workspace/review-claude-config/skills/review-claude-config/references/review-report-contract.md) as the only relevant contract authorities in this area.
- Before finalizing edits, search for non-canonical class names in `docs/` and `research/`.

## Ongoing Maintenance

- keep [`engineering-baseline.md`](/home/nos-ai/workspace/review-claude-config/skills/review-claude-config/references/engineering-baseline.md) explicitly evidence-classified
- keep the baseline refresh path aligned with the canonical evidence contract and shared source-quality criteria
- keep maintainer guidance files such as [`CLAUDE.md`](/home/nos-ai/workspace/review-claude-config/CLAUDE.md) consistent with the active evidence vocabulary and runtime behavior
