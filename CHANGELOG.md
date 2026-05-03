# Changelog

All notable changes to this plugin are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this plugin adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-05-03

**Internal layout — selective hub consolidation per Rule of Three.** Six reference files with ≥3 cross-skill consumers migrated from their owner skills into the central hub at `skills/review-claude-config/references/`. Reference files with 0–2 consumers remain skill-local (Locality of Behaviour over premature DRY). Plugin API is unchanged — additive minor bump.

### Changed

- Migrated to hub: `merge-rules.md` (5 consumers), `commit-conventions.md` (5), `signal-catalog.md` (4), `report-schema.md` (4), `mcp-evaluation-guide.md` (3), `agent-evaluation-guide.md` (3).
- All 48 path references in skills, agents, docs, scripts, tests, research updated to the new hub path. Frozen test fixtures (`tests/fixtures/{rubric_evaluator,agent_outputs}/**`) intentionally untouched to preserve determinism guarantees.
- `CLAUDE.md` §Architecture documents the Rule-of-Three hub-inclusion threshold.
- `skills/check-repo-health/references/cross-skill-dependencies.md` `last_refreshed` bumped to reflect the new hub state.

### Migration for external consumers

If your own memory, plans, or notes reference the migrated files at their old paths, run:

```bash
grep -rn "skills/\(review-skill\|apply-review-findings\|suggest-skills\|review-analytics\|review-mcp-server\|review-agent\)/references/\(merge-rules\|commit-conventions\|signal-catalog\|report-schema\|mcp-evaluation-guide\|agent-evaluation-guide\)" \
  $HOME/.claude/projects/<your-project>/
```

and update each hit to `skills/review-claude-config/references/<file>.md`.

## [2.0.0] - 2026-05-03

**Breaking — plugin renamed.** `skill-quality` → `claude-config`. The previous name implied skill-only quality review, but the suite covers all Claude Code primitives (skills, agents, rules, hooks, MCP servers, plugins, settings.json, CLAUDE.md) and runtime artefacts (session traces, memory, trust chains, policy compliance). The new name reflects the actual scope, and the slash-command namespace becomes `claude-config:<command>` (no more stuttering with `:review-claude-config`).

### Migration

Existing installations must reinstall — `claude plugin update` does not migrate plugin renames:

```bash
claude plugin uninstall skill-quality
claude plugin marketplace update
claude plugin install claude-config@ntbc-plugins
```

User data under `${HOME}/.claude/plugins/data/skill-quality/` is preserved on uninstall but lives at the old path; rename it to `${HOME}/.claude/plugins/data/claude-config/` to keep historical reports and audit traces accessible to the new install.

### Changed

- `.claude-plugin/plugin.json` — `name` field, version, description (now lists all covered primitive types).
- `.claude-plugin/marketplace.json` — plugin entry name, version, ref, description, tags.
- `README.md` — install / update / uninstall / cache-path examples.
- `CLAUDE.md` — architecture description, data path references.
- `install.sh` — `PLUGIN_NAME` constant.
- `docs/cross-repo-probe-runbook.md` — install / probe commands.
- `tests/test_merge_findings.py`, `tests/test_perspective_replay.py` — namespace example updates.
- `.claude/settings.local.json` — local data-path permissions updated to new path.

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

[2.0.0]: https://github.com/Nosmoht/review-claude-config/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/Nosmoht/review-claude-config/compare/v1.0.2...v1.1.0

## [1.0.2] - 2026-04-30

- research-index extraction; rubric refinements landed pre-audit.

## [1.0.1] - 2026-04

- Plugin distribution active via `claude plugin install skill-quality@ntbc-plugins`.

## [1.0.0] - 2026-04

- Initial public release.
