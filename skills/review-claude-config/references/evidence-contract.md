---
name: evidence-contract
description: Canonical claim-classification contract for repository-level evidence, source precedence, and contradiction handling
---

# Evidence Contract

Use this file as the only canonical contract for classifying repository-level claims.

## Canonical Classes

- **Proven result**: directly supported by Tier 1 evidence such as official documentation, specifications, benchmark papers, or primary research.
- **Engineering guidance**: supported by official operational guidance or credible technical literature, but not established as a strong comparative result.
- **Repo default**: a local repository policy, threshold, or convention chosen for maintainability or workflow reasons rather than settled science.
- **Low-evidence area**: a useful but weakly validated design area where direct literature or authoritative guidance is limited.

## Source Precedence

When multiple evidence sources exist, apply this order:

1. Tier 1 sources
2. Tier 2 sources
3. Local `research/*` summaries

Local summaries are reusable repo evidence but are not the final authority when a fresher or stronger primary source disagrees.

## Contradiction Handling

- Record contradictions explicitly.
- Do not rewrite a contradiction into a single confident claim unless the stronger source clearly resolves it.
- If a contradiction remains unresolved, the claim must be downgraded from `Proven result` to either `Engineering guidance`, `Repo default`, or `Low-evidence area`, whichever matches the remaining certainty.

## Claim Rules

- Scientific or generalizable claims require a source-backed basis.
- Numeric thresholds, defaults, and workflow conventions that are not directly benchmark-backed must be labeled `Repo default`.
- Novel or heuristic subsystems with thin evidence must be labeled `Low-evidence area`.
- Documentation should point to this file rather than inventing alternate class names.

## Vocabulary Mapping

Use these mappings when normalizing older wording:

| Older wording | Canonical class |
|---|---|
| Local design preference | Repo default |
| Local policy | Repo default |
| Heuristic / novel contribution / limited evidence | Low-evidence area |

## Intended Consumers

- Repository-level research artifacts in `docs/`
- Shared reference files under `skills/review-claude-config/references/`
- Future health checks and documentation consistency checks
