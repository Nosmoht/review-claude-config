---
name: goal-alignment-research-index
description: Index of Goal Alignment failure-mode research files; load when reviewing Goal Alignment dimension or designing GA-* rubric items
last_refreshed: 2026-04-29
---

# Goal Alignment Research Index

Goal Alignment is the highest-weighted dimension in the Review Suite (20%). Three Tier-1-evidenced failure-mode clusters expand the dimension's coverage beyond GA-X (checkpoint-decomposition).

## Cluster Files

| Cluster | File | Primary Tier-1 Sources | Operationalization |
|---|---|---|---|
| **Sycophancy** | [sycophancy.md](sycophancy.md) | arXiv:2310.13548 (Sharma/Anthropic ICLR 2024), arXiv:2502.08177 (SycEval) | Skill body acts on user-supplied premise without verification predicate → Goal Alignment capped at C |
| **Goal Misgeneralization** | [goal-misgeneralization.md](goal-misgeneralization.md) | arXiv:2105.14111 (Langosco/ICML 2022), arXiv:2210.01790 (Shah/DeepMind) | Skill success criteria use form-only proxies without function-level intent verification → Goal Alignment capped at C |
| **Specification Gaming** | [specification-gaming.md](specification-gaming.md) | arXiv:2502.13295 (Bondarenko), arXiv:2505.07846 (Winning at All Cost) | Self-review-class skills with regex-only criteria and no evidence-grounding requirement → Goal Alignment capped at C (advisory) |

## Dimension Coverage Before vs. After

| Aspect | Before (#92) | After (#92) |
|---|---|---|
| Tier-1 sources cited in rubric | 2 (GA-X) | ≥6 (GA-X + 5 from new clusters) |
| Failure-mode clusters covered | 1 (checkpoint-decomposition) | 4 |
| Dedicated research files | 0 | 3 + this index |
| Coverage breadth | Narrow | Broad |

See [docs/dimension-evidence-coverage.md](../../docs/dimension-evidence-coverage.md) for full per-dimension coverage matrix.

## Distinction Map

The four Goal-Alignment failure modes are *orthogonal* — a single skill can fail on multiple axes:

- **GA-X (existing)**: omits *intermediate* domain-expert checkpoints (Langosco-adjacent: agent skips diagnostic step that would catch goal-drift).
- **Sycophancy**: acts on *user-supplied premise* without verification (deference-induced misalignment).
- **Goal Misgeneralization**: defines success in *form* not *function* (proxy-induced misalignment).
- **Specification Gaming**: optimizes for *passing checks* not *achieving intent* (criteria-induced misalignment, esp. in self-review skills).

A skill that fails on Sycophancy will accept user-supplied bad input without protest. A skill that fails on Goal Misgeneralization will produce well-formed but functionally-empty output. A skill that fails on Specification Gaming will produce output that satisfies the rubric without grounding it.

## Self-Application Audit (2026-04-29)

Three flagship skills audited against the new GA-Y / GA-Z / GA-S items:

| Skill | GA-Y (Premise Verification) | GA-Z (Function-Level Goal) | GA-S (Anti-Gaming) | Result |
|---|---|---|---|---|
| `skills/review-skill/SKILL.md` | PASS — line 24 explicit `$ARGUMENTS` validation (file exists, `*.md` pattern, YAML frontmatter with `name` field) | PASS — success criteria include "every High/Medium finding cites ≥1 verbatim quote (evidence-citation predicate)" + convergence predicate | PASS — review-class with mandatory evidence-grounding + cross-run convergence | All pass |
| `skills/audit-repo/SKILL.md` | PASS — line 19 "Validate the folder exists and contains files" | FAIL → PASS (fixed in #100): completion criteria at lines 158 + 244 now require either ≥1 path/filename citation per category OR explicit "no instances found" with attempted Glob/Bash pattern | NA (audit-class, advisory only) | Resolved |
| `skills/scaffold-skill/SKILL.md` | NEEDS-FOLLOW-UP — `$ARGUMENTS` parsed at line 20 but full validation chain not inspected in initial scan | NEEDS-FOLLOW-UP | NA (scaffold-class) | Partial |

**Action:** GA-Z violation in `audit-repo` triggers a follow-up issue to add evidence-citation requirement to its completion criteria (path quoted per category, or per-finding citation). Tracked separately to keep this PR scoped to introduction-of-rubric-items.

## Cross-Validation Posture

All three clusters meet the web-research rule (`~/.claude/workspace/claude-config/rules/web-research.md`): 2+ independent sources, ≥1 Tier-1, peer-reviewed or foundation-lab provenance. None of the cited sources is older than the 18-month freshness cutoff (oldest: Langosco 2022 — exempt as foundational paper with no superseding revision).
