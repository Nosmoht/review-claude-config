# Changelog

All notable changes to this plugin are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this plugin adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-05-02

Interim ship of accumulated fixes and feature additions before the GA-cut at v1.2.0. Includes 5 user-visible features, 4 rubric-evaluator fixes that change FAIL verdicts, and 4 policy-gate / hook-discipline fixes.

### Added

- **Phase 7.6 spillover verification gate** in the `/implement-issue` workflow. Filed spillover issues now require byte-equivalent sample-evidence with the evaluator trace before being accepted.
- **Declarative apply-risk decision matrix** for `/apply-*-findings` skills — risk classification per finding now drives the gate behavior.
- **Pattern-based MCP tool classification** in the policy-gate. Distinguishes L1 reads from L4 mutations across MCP server families instead of relying on prefix matching.
- **Perspective-agent ownership tables extended to the agent-rubric namespace.** `/review-perspective-{clarity,correctness,integration}` agents now cover both skill and agent rubric items consistently.
- **Reviewer-side threat model** documented at `docs/meta-review-threat-model.md`. Captures meta-review threats (poisoned skill content, stale evidence, finding-poisoning) separate from the subject-side `injection-surface-catalog.md`.

### Changed

- **Rubric — CE-X** trigger narrowing + `compact` as noun marked NA. Reduces FAIL count ~11 → 1 across the suite.
- **Rubric — RL-4b** internal-report-path marked NA + helper renamed for clarity. Reduces FAIL count ~8 → 2.
- **Rubric — IJ-1b** validation-pattern set + fallback-NA. Reduces FAIL count ~19 → 1.
- **Hooks** — classified by event family with retention/redaction policy at `docs/hook-governance.md`; descriptions in `hooks.json` cross-reference the policy.
- **`apply-risk-decision-matrix`** documentation now distinguishes a declarative risk taxonomy from prior ad-hoc severity classification.

### Fixed

- **Policy-gate** — close MCP prefix-collision gap; tighten the test surface against the verb set.
- **Policy-gate** — switch to token matching against the L4 verb set instead of substring matching.
- **Hooks** — harden exit-code discipline against the upstream phantom-block class (anthropics/claude-code#21988); add subprocess coverage.
- **`audit-context-budget`** — add Phase 3 validation step to satisfy the GA-X checkpoint-decomposition rubric item.
- **Lint** — remove unused pytest import; rename an unused template variable.

### Reverted

- **Rubric — SP-2b regex extension** (originally landed in 1160e8a). Empirical falsification via spike showed zero PASS-flips. The genuine path is per-skill binding language; rolls forward to issue #90.

### Documentation

- Cross-referenced redaction policy in `hooks.json` descriptions.
- Tier-A justification + credential-scope Hard Rules added to `agents/review-perspective-*.md`.
- External academic-style review committed at `docs/audits/`.
- Audit-followup roadmap items 4a/4b added to the refactor-plan.
- Pronoun-antecedent fix in `review-skill` SKILL.md (residual CLAR-2 from #121).
- Pattern-based MCP classification documented in `docs/audit/`.

### Build & infrastructure

- Untrack `settings.local.json`; remove stale lock file.

[1.1.0]: https://github.com/Nosmoht/review-claude-config/compare/v1.0.2...v1.1.0

## [1.0.2] - 2026-04-30

- research-index extraction; rubric refinements landed pre-audit.

## [1.0.1] - 2026-04

- Plugin distribution active via `claude plugin install skill-quality@ntbc-plugins`.

## [1.0.0] - 2026-04

- Initial public release.
