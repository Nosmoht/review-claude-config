# Changelog

All notable changes to this plugin are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this plugin adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.12.1](https://github.com/Nosmoht/review-claude-config/compare/v2.12.0...v2.12.1) (2026-05-26)


### Changed

* **skill/apply-*, docs:** fix recursive schema defect + arch-doc arithmetic ([2697bd9](https://github.com/Nosmoht/review-claude-config/commit/2697bd9fa650f809cfeb8de9ec1f242d24d5bf53))
* **skill/apply-*:** fix stale template ref + document claimed.json schema ([9a5dafe](https://github.com/Nosmoht/review-claude-config/commit/9a5dafe2282087d95042c5329056be3499c0a376))
* **skill/apply-*:** replace adversarial-critic Layer B with structural primitives ([36b92a9](https://github.com/Nosmoht/review-claude-config/commit/36b92a9c810e13b53385c573a0e7bfcf9575969e))
* **skill/audit-*:** gate Layer B on predicate-density per right-altitude ([dec705c](https://github.com/Nosmoht/review-claude-config/commit/dec705c24f4c3c4100d065827781978c8c5db4a8))
* **skill/audit-*:** replace 30% threshold with criteria-based Layer-B-Gate ([c14cb79](https://github.com/Nosmoht/review-claude-config/commit/c14cb79cd5f0dd7d87f08319f8ce26a15fd03625))
* **skill/maintain-*:** drop redundant Layer B+C per right-altitude ([f7cff18](https://github.com/Nosmoht/review-claude-config/commit/f7cff186baa85851f9138613cab20f38215ccdb2))
* **skill/scaffold-*:** drop redundant Layer B+C per right-altitude ([50e1844](https://github.com/Nosmoht/review-claude-config/commit/50e18444ebbb0fa3b8bf9816dec020860e3598d1))

## [2.12.0](https://github.com/Nosmoht/review-claude-config/compare/v2.11.1...v2.12.0) (2026-05-26)


### Changed

* **skill/apply-agent-review-findings:** add 3-layer verification pipeline ([1a69f54](https://github.com/Nosmoht/review-claude-config/commit/1a69f5432e0825d7da78adefe7cc1addd3cbc61f))
* **skill/apply-audit-findings:** add 3-layer verification pipeline ([61a6ced](https://github.com/Nosmoht/review-claude-config/commit/61a6cedb9333d6112c653c7155cd62d0656d26db))
* **skill/apply-review-findings:** add 3-layer verification pipeline ([5e9f858](https://github.com/Nosmoht/review-claude-config/commit/5e9f858ff52621c0751633c35a2b1a6c7ccc09c3))
* **skill/apply-rule-review-findings:** add 3-layer verification pipeline ([2f8e358](https://github.com/Nosmoht/review-claude-config/commit/2f8e358988a4bc5dd10f061dca91936644b543c5))
* **skill/apply-skill-review-findings:** add 3-layer verification pipeline ([3df526f](https://github.com/Nosmoht/review-claude-config/commit/3df526ff3154c1e170330f4ea86738c39ee042f3))
* **skill/audit-context-budget:** add 3-layer verification pipeline ([bd82a77](https://github.com/Nosmoht/review-claude-config/commit/bd82a7766655101cff75630564bac0f2ae968d34))
* **skill/audit-mcp-auth:** add 3-layer verification pipeline ([8190e57](https://github.com/Nosmoht/review-claude-config/commit/8190e570c16986daa13edc88b7d5e725e50f1eae))
* **skill/audit-memory-hygiene:** add 3-layer verification pipeline ([a3d7b9e](https://github.com/Nosmoht/review-claude-config/commit/a3d7b9e935a4a80c8121f97a22b52d23e15a4df7))
* **skill/audit-policy-compliance:** add 3-layer verification pipeline ([a05d88d](https://github.com/Nosmoht/review-claude-config/commit/a05d88dd50443d3f0e630375ba7c7787528061e9))
* **skill/audit-repo:** add 3-layer verification pipeline ([00dd89a](https://github.com/Nosmoht/review-claude-config/commit/00dd89a98cad76949bfb4172de07d9afc80d7e68))
* **skill/audit-trust-chain:** add 3-layer verification pipeline ([edbf7f5](https://github.com/Nosmoht/review-claude-config/commit/edbf7f5b24f25a1bc5c26ca6aee7251e08e4bcae))
* **skill/check-repo-health:** add 3-layer verification pipeline ([f43ca61](https://github.com/Nosmoht/review-claude-config/commit/f43ca61f9979128c5f94f316278e87d6f852cb63))
* **skill/classify-trace-errors:** add 3-layer verification pipeline ([163ff14](https://github.com/Nosmoht/review-claude-config/commit/163ff14df7d4dedebf1ca44285a370af769ca602))
* **skill/develop-hooks:** add 3-layer verification pipeline ([5563dad](https://github.com/Nosmoht/review-claude-config/commit/5563dad7a0e94ba22fac06c3c02e013892aaa047))
* **skill/maintain-evidence-layer:** add 3-layer verification pipeline ([e2e3171](https://github.com/Nosmoht/review-claude-config/commit/e2e317136e11c8358d9967b3a2ed7127ec740902))
* **skill/refresh-engineering-baseline:** add 3-layer verification pipeline ([0df4b85](https://github.com/Nosmoht/review-claude-config/commit/0df4b8501af7d713a432552e6d7f68f502a235e5))
* **skill/refresh-evidence-coverage:** add 3-layer verification pipeline ([4844485](https://github.com/Nosmoht/review-claude-config/commit/484448542a8a1caf65e21687b3beab32d050cf1c))
* **skill/review-agent:** add 3-layer verification pipeline ([508c62e](https://github.com/Nosmoht/review-claude-config/commit/508c62e83e65c58d46c8fba83401284075e58136))
* **skill/review-analytics:** add 3-layer verification pipeline ([324d458](https://github.com/Nosmoht/review-claude-config/commit/324d4582915b9e4e3b9064771b580f0d5bff7257))
* **skill/review-claude-config:** add 3-layer verification pipeline ([49e25e5](https://github.com/Nosmoht/review-claude-config/commit/49e25e55310303c77f93f021a702516e6efa0d9a))
* **skill/review-claude-md:** add 3-layer verification pipeline ([fef707f](https://github.com/Nosmoht/review-claude-config/commit/fef707f379051a81f244d5a9d5f3e41a05c82672))
* **skill/review-domain-currency:** add 3-layer verification pipeline ([b73d96a](https://github.com/Nosmoht/review-claude-config/commit/b73d96a951fbae1e00e34b09e37e038f445cece4))
* **skill/review-mcp-server:** add 3-layer verification pipeline ([9bcd0b8](https://github.com/Nosmoht/review-claude-config/commit/9bcd0b8c101e1c75b5dd8d5b7d6f6029a831542a))
* **skill/review-plugin:** add 3-layer verification pipeline ([ce45df5](https://github.com/Nosmoht/review-claude-config/commit/ce45df55b2617f53a1baf228e968ed79edf8eed1))
* **skill/review-rule:** add 3-layer verification pipeline ([5a338b6](https://github.com/Nosmoht/review-claude-config/commit/5a338b6342e36e46e236a7a7981d8b30c2ed47b8))
* **skill/review-session-trace:** add 3-layer verification pipeline ([36f5739](https://github.com/Nosmoht/review-claude-config/commit/36f5739a769c1acf9ebe0f9597ad564931aadc21))
* **skill/review-settings:** add 3-layer verification pipeline ([963b997](https://github.com/Nosmoht/review-claude-config/commit/963b997a6322a02b873dd6d3ae8fe89abc571545))
* **skill/review-skill:** add 3-layer verification pipeline ([e7ac57f](https://github.com/Nosmoht/review-claude-config/commit/e7ac57fb2290805f31a74dd54268e8646b852707))
* **skill/run-eval-cases:** add 3-layer verification pipeline ([5ce1b3f](https://github.com/Nosmoht/review-claude-config/commit/5ce1b3fff0e4d08841215362d96b6225a768b368))
* **skill/scaffold-agent:** add 3-layer verification pipeline ([1601085](https://github.com/Nosmoht/review-claude-config/commit/1601085c5617ffa1844ca3f27aa2ae6e0814608c))
* **skill/scaffold-mcp-server:** add 3-layer verification pipeline ([8eb7278](https://github.com/Nosmoht/review-claude-config/commit/8eb727807058f9da1809297a4b9783b47cedf544))
* **skill/scaffold-rule:** add 3-layer verification pipeline ([b5d8505](https://github.com/Nosmoht/review-claude-config/commit/b5d850578a954104e3fc25b277121aae7992a0ab))
* **skill/scaffold-skill:** add 3-layer verification pipeline ([4e58690](https://github.com/Nosmoht/review-claude-config/commit/4e58690f24fbb0bb10e0ff3298302c77ddb5178e))
* **skill/suggest-skills:** add 3-layer verification pipeline ([04d2db7](https://github.com/Nosmoht/review-claude-config/commit/04d2db71248be6294c98d3bb2781ed1a1472d23a))
* **skill/sync-research-index:** add 3-layer verification pipeline ([b5d65ff](https://github.com/Nosmoht/review-claude-config/commit/b5d65ffcb6493fbd2bd5253104a0a1415efae9ff))
* **skill/validate-primitive-dependencies:** add 3-layer verification pipeline ([126c7fb](https://github.com/Nosmoht/review-claude-config/commit/126c7fb9aca577a54cc505154c658b7ece416620))


### Fixed

* **skill/apply-skill-review-findings:** downgrade allowed_tools_unused to SOFT ([b79a167](https://github.com/Nosmoht/review-claude-config/commit/b79a16779d7c00b30f5905e57a3fceeca07dad5a))
* **skill/refresh-engineering-baseline:** decouple D1 from unverifiable predicate ([c0b4e00](https://github.com/Nosmoht/review-claude-config/commit/c0b4e009f12c946bade02923092263f95251462b))
* **skill/review-domain-currency:** correct Layer A S1 timing ([df628ac](https://github.com/Nosmoht/review-claude-config/commit/df628ac02d889b6567b50aaba173e0865ceab199))

## [2.11.1](https://github.com/Nosmoht/review-claude-config/compare/v2.11.0...v2.11.1) (2026-05-13)


### Changed

* **rubric:** remove 3 SEMANTIC binary items (PE-1, PE-2, CLAR-1) ([3b9604b](https://github.com/Nosmoht/review-claude-config/commit/3b9604b9db0860f7f4a50ae308a853176df861a8))


### Fixed

* **provenance:** correct fabricated arXiv-ID + magnitude across 9 files ([c9f1500](https://github.com/Nosmoht/review-claude-config/commit/c9f15008ae1e3c37c2e0d5687964e776ec92040b))

## [2.11.0](https://github.com/Nosmoht/review-claude-config/compare/v2.10.1...v2.11.0) (2026-05-13)


### Changed

* **skills:** tighten descriptions for 5 weak-trigger skills ([#271](https://github.com/Nosmoht/review-claude-config/issues/271)) ([183b8db](https://github.com/Nosmoht/review-claude-config/commit/183b8dbd8bdb2cc3564e5f1707fa2fcada7d239d))

## [2.10.1](https://github.com/Nosmoht/review-claude-config/compare/v2.10.0...v2.10.1) (2026-05-09)


### Fixed

* **skills:** unify repo-slug resolution via bin/repo-slug.sh ([#162](https://github.com/Nosmoht/review-claude-config/issues/162)) ([#252](https://github.com/Nosmoht/review-claude-config/issues/252)) ([e5a2403](https://github.com/Nosmoht/review-claude-config/commit/e5a240355d25bbea3d9b59ebc5fa055c5b6b6e87))

## [2.10.0](https://github.com/Nosmoht/review-claude-config/compare/v2.9.0...v2.10.0) (2026-05-08)


### Changed

* **scripts:** description-graph validator + suite self-audit ([#217](https://github.com/Nosmoht/review-claude-config/issues/217)) ([#250](https://github.com/Nosmoht/review-claude-config/issues/250)) ([123285a](https://github.com/Nosmoht/review-claude-config/commit/123285afdb8abb054aa5f3beab0722f151a0908b))

## [2.9.0](https://github.com/Nosmoht/review-claude-config/compare/v2.8.0...v2.9.0) (2026-05-07)


### Changed

* **references:** add DQ-1..DQ-6 sub-rubric + description conventions ([#226](https://github.com/Nosmoht/review-claude-config/issues/226)) ([a64d60e](https://github.com/Nosmoht/review-claude-config/commit/a64d60e5532bc5d6f238a3ef680c824ebc173244)), closes [#216](https://github.com/Nosmoht/review-claude-config/issues/216)

## [2.8.0](https://github.com/Nosmoht/review-claude-config/compare/v2.7.1...v2.8.0) (2026-05-07)


### Changed

* **references:** add description-design-problem reference ([#215](https://github.com/Nosmoht/review-claude-config/issues/215)) ([#224](https://github.com/Nosmoht/review-claude-config/issues/224)) ([d9b1907](https://github.com/Nosmoht/review-claude-config/commit/d9b1907c8e59b1fcc6eb6194c05b49ace96ed84f))

## [2.7.1](https://github.com/Nosmoht/review-claude-config/compare/v2.7.0...v2.7.1) (2026-05-07)


### Fixed

* **skills:** swap Tavily MCP for Claude Code WebSearch in review-domain-currency ([#220](https://github.com/Nosmoht/review-claude-config/issues/220)) ([0c544e0](https://github.com/Nosmoht/review-claude-config/commit/0c544e07d46a7eec0c0b6f95f10df1bac003968b))

## [2.7.0](https://github.com/Nosmoht/review-claude-config/compare/v2.6.0...v2.7.0) (2026-05-07)


### Changed

* **skills:** add review-domain-currency advisory skill + domain-researcher agent ([#213](https://github.com/Nosmoht/review-claude-config/issues/213)) ([43f35a9](https://github.com/Nosmoht/review-claude-config/commit/43f35a9719c22565452d78a7203598914e7b4f30))

## [2.6.0](https://github.com/Nosmoht/review-claude-config/compare/v2.5.0...v2.6.0) (2026-05-07)


### Changed

* **scripts:** add SF-3 peer-reference body-check for agent rubric ([#211](https://github.com/Nosmoht/review-claude-config/issues/211)) ([901c148](https://github.com/Nosmoht/review-claude-config/commit/901c14826c977fb45dafd31e7830b3a8c87acf44))

## [2.5.0](https://github.com/Nosmoht/review-claude-config/compare/v2.4.4...v2.5.0) (2026-05-07)


### Changed

* **rules:** add R5 — AC-necessity gate per ISO/IEC/IEEE 29148:2018 ([#208](https://github.com/Nosmoht/review-claude-config/issues/208)) ([7178938](https://github.com/Nosmoht/review-claude-config/commit/717893808d6e5cc6220d801fd00ef37cafdb4cd9))

## [Unreleased]


### Changed

* **scripts:** right-altitude closeout — doc-sweep replaces stale `merge_findings.py` SoT pointers with `merge-policy.yaml` and `scoring-rubric.md` references ([#193](https://github.com/Nosmoht/review-claude-config/issues/193))


## [2.4.4](https://github.com/Nosmoht/review-claude-config/compare/v2.4.3...v2.4.4) (2026-05-06)


### Changed

* **scripts:** thin readers for validate_schema + validate_token_budgets (Stufe 3) ([#201](https://github.com/Nosmoht/review-claude-config/issues/201)) ([7375ad1](https://github.com/Nosmoht/review-claude-config/commit/7375ad13cf9716b43c05d42365ef1b138077c995))

## [2.4.3](https://github.com/Nosmoht/review-claude-config/compare/v2.4.2...v2.4.3) (2026-05-04)


### Changed

* **session_check:** extract 2 constants to JSON + schema ([#195](https://github.com/Nosmoht/review-claude-config/issues/195)) ([89eb885](https://github.com/Nosmoht/review-claude-config/commit/89eb8854dbdb4fc451ae32dde90afa001cb1860c))

## [2.4.2](https://github.com/Nosmoht/review-claude-config/compare/v2.4.1...v2.4.2) (2026-05-04)


### Changed

* **policy_gate:** lazy-load 5 policy constants from json ([2cdbcd0](https://github.com/Nosmoht/review-claude-config/commit/2cdbcd0c6c169eac38417a59e649bdaf15cd9cf6))

## [2.4.1](https://github.com/Nosmoht/review-claude-config/compare/v2.4.0...v2.4.1) (2026-05-04)


### Changed

* **merge_findings:** lazy-load 5 policy constants from yaml ([3a5e168](https://github.com/Nosmoht/review-claude-config/commit/3a5e1686e11a4efdf428721de1653845108a8d3b))

## [2.4.0](https://github.com/Nosmoht/review-claude-config/compare/v2.3.3...v2.4.0) (2026-05-04)


### Changed

* **policy:** regenerate merge-policy.yaml from scoring-rubric.md ([e119169](https://github.com/Nosmoht/review-claude-config/commit/e1191698460fe58422f6ca58de59c32b0b640c87))

## [2.3.3](https://github.com/Nosmoht/review-claude-config/compare/v2.3.2...v2.3.3) (2026-05-04)


### Changed

* **rubric:** scoring-rubric becomes single SOT for merge-policy data ([fd036fe](https://github.com/Nosmoht/review-claude-config/commit/fd036fe33ec61f3731dfd8f6b277e6bad60ffc2f))

## [2.3.2](https://github.com/Nosmoht/review-claude-config/compare/v2.3.1...v2.3.2) (2026-05-04)


### Changed

* **bin:** move sync-marketplace-ref to bash per deterministic-hierarchy ([#181](https://github.com/Nosmoht/review-claude-config/issues/181)) ([b8c20fe](https://github.com/Nosmoht/review-claude-config/commit/b8c20fe32bf46a8c67ec7bda0f9c79913d2b7fe5))

## [2.3.1](https://github.com/Nosmoht/review-claude-config/compare/v2.3.0...v2.3.1) (2026-05-04)


### Fixed

* **ci:** guard fromJSON against empty release-please pr output ([#179](https://github.com/Nosmoht/review-claude-config/issues/179)) ([0633006](https://github.com/Nosmoht/review-claude-config/commit/0633006933fbab63c7444d0ff7ba4950aff2ecf7))

## [2.3.0](https://github.com/Nosmoht/review-claude-config/compare/v2.2.0...v2.3.0) (2026-05-04)


### Changed

* **ci:** auto-merge release PRs and tag on merge ([#177](https://github.com/Nosmoht/review-claude-config/issues/177)) ([0fd11a6](https://github.com/Nosmoht/review-claude-config/commit/0fd11a63d974801bd1ff248b561abd0b361fbb5c))

## [2.2.0](https://github.com/Nosmoht/review-claude-config/compare/v2.1.0...v2.2.0) (2026-05-04)


### Changed

* **ci:** auto-release on push to main via release-please ([#172](https://github.com/Nosmoht/review-claude-config/issues/172)) ([099cc4c](https://github.com/Nosmoht/review-claude-config/commit/099cc4c29763756d22fcb1e0143d7cac64d1b4ae))
* **scaffold:** harden scaffold-skill + scaffold-agent for rubric coverage ([#170](https://github.com/Nosmoht/review-claude-config/issues/170)) ([9914b7c](https://github.com/Nosmoht/review-claude-config/commit/9914b7c19d54b44bab50a67850fb23ca60f76e7e))
* **skills:** add Agent and Rule signal tables to signal-catalog ([#165](https://github.com/Nosmoht/review-claude-config/issues/165)) ([e521e3c](https://github.com/Nosmoht/review-claude-config/commit/e521e3c49df20dc37d07acbe842565d1ecc544b1))

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
