# audit-repo

Analyze any repository to identify what Claude Code primitives (CLAUDE.md sections, skills, agents, hooks, rules) it needs. Uses two sub-agents for static analysis and token efficiency measurement, then derives an intervention matrix with prioritized recommendations. The derivation layer is evidence-informed, but parts of it remain heuristic or repo-policy driven rather than benchmark-settled science.

## Overview

| Property | Value |
|----------|-------|
| **Name** | audit-repo |
| **Location** | `skills/audit-repo/SKILL.md` |
| **Type** | Discovery |
| **Allowed Tools** | Agent, Read, Write, Glob, Grep, WebSearch, WebFetch |
| **disable-model-invocation** | true |
| **Argument Hint** | `[folder]` |
| **Mode** | Standalone only |

## Purpose

The skill performs a comprehensive static analysis of any repository to answer: "What Claude Code primitives does this repo need, and why?" It examines the repository's toolchain, architecture, naming conventions, linter coverage, domain knowledge artifacts, and token efficiency characteristics. From these signals it derives a prioritized intervention matrix mapping error classes to specific primitives (CLAUDE.md sections, skills, agents, hooks, rules), each backed by concrete evidence from the scan and labeled with an evidence class and confidence level.

The skill is strictly read-only on the target repository. It writes only the final audit report to `.claude/reviews/`. It does not generate any primitives -- it produces a diagnostic matrix that other skills (`/scaffold-skill`, `/suggest-skills`) can act on.

## Process Steps

### Phase 1 -- Setup

**Step 0: Tool availability checks.** The skill attempts a trivial WebSearch query to test whether WebSearch is available, then a trivial WebFetch to test that tool. Results are stored as `websearch_available` and `webfetch_available` flags. These determine whether optional web validation occurs in Phase 5.

**Step 1: Load references.** The skill reads six reference files:

- `references/signal-patterns.md` -- file patterns to look for in each analysis step
- `references/error-class-taxonomy.md` -- error classes and their mapping to primitive types
- `references/primitive-decision-matrix.md` -- decision rules for selecting primitive types
- `references/token-heuristics.md` -- thresholds and scoring formulas for token analysis
- `references/audit-report-schema.md` -- report frontmatter and body structure

It also reads one reference from the `suggest-skills` sibling skill:

- `references/signal-catalog.md` -- signal tables for skill gap detection

**Step 2: Initial target assessment.** The skill checks the target folder for existing Claude Code infrastructure: CLAUDE.md presence, `.claude/skills/` directory, agents, rules, and hooks. This baseline informs which gaps Phase 4 can identify.

### Phase 2 -- Static Repo Analysis (Repo Scanner Agent)

A sub-agent is launched with tools: Glob, Grep, Read, Bash. Scan limits are enforced: 50 lines per file read, 4 directory levels deep, 500 files per directory listing, and Bash is restricted to read-only commands.

The agent performs five analysis categories:

**A: Toolchain Detection.** Identifies build tools, test runners, deploy scripts, and CI pipelines by scanning package.json `scripts`, Makefile targets, CI configuration files (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`), and similar toolchain markers.

**B: Ambiguity Measurement.** Measures structural complexity: maximum directory depth, maximum files per directory, naming collisions (files with identical basenames in different directories), and computes an overall sprawl score.

**C: Linter/Formatter Coverage.** Classifies each linter/formatter found into one of four tiers:
- **Deterministic** -- runs automatically with deterministic output (e.g., Prettier, Black)
- **CI-enforced** -- runs in CI and blocks merges (e.g., ESLint in CI)
- **AI-instructed** -- referenced in CLAUDE.md or instructions but not automated
- **Undocumented** -- config file present but not referenced in CI or instructions

**D: Architecture Pattern Extraction.** Detects architectural patterns from directory signatures (e.g., `src/domain/`, `src/infrastructure/`), dependency injection markers, Architecture Decision Records (ADRs), and import direction analysis.

**E: Domain Knowledge Inventory.** Catalogs domain-specific artifacts: OpenAPI/Swagger specs, protobuf definitions, GraphQL schemas, glossary files, ADRs, database migrations, JSON schemas, and other domain knowledge sources.

### Phase 3 -- Token Efficiency Analysis (Token Analyzer Agent)

A second sub-agent is launched with tools: Glob, Bash, Read. The same scan limits apply.

The agent computes five metrics:

**A: File Size Distribution.** Identifies the largest source files and classifies them by severity:
- **Severe** (>2000 lines) -- likely to consume excessive context on every read
- **Critical** (>1000 lines) -- significant token cost, splitting recommended
- **Token sink** (>500 lines) -- moderate cost, worth monitoring

**B: Navigation Sprawl Score.** Computed as `depth x max_files x collisions`. Interpretation:
- **>100** -- P0 intervention needed (navigation instructions in CLAUDE.md)
- **30--100** -- selective navigation hints recommended
- **<30** -- no navigation intervention needed

**C: Build Error Verbosity.** Maps each detected toolchain to its expected error output verbosity and estimates token cost per build failure. High-verbosity toolchains (e.g., TypeScript with strict mode, Rust) flag the need for error-filtering hooks or rules.

**D: Monorepo Scope Isolation.** Counts workspace packages (from workspace configs in package.json, pnpm-workspace.yaml, Cargo.toml, etc.) and detects cross-package import patterns. Poor isolation suggests scope-limiting CLAUDE.md sections.

**E: Context Burn Rate.** Estimates tokens consumed per common task type (bug fix, new feature, refactor) based on the repository's file sizes, depth, and toolchain verbosity.

### Phase 4 -- Primitives Derivation (inline, not sub-agent)

This phase runs inline in the top-level skill (not delegated to a sub-agent). It synthesizes findings from Phases 2 and 3 into four derivation branches:

**4A: CLAUDE.md Gaps.** Checks whether the repository's CLAUDE.md (if any) covers six areas: Toolchain (build/test/deploy commands), Architecture (directory layout and patterns), Scope (monorepo boundaries), Domain (key terminology and schemas), Navigation (how to find things), and Large files (files that need special handling). Each uncovered area becomes a gap with a specific CLAUDE.md section recommendation.

**4B: Skill Candidates.** Identifies potential skills through two methods: (1) structural repetition in the codebase (repeated multi-step patterns that could be automated), and (2) signal catalog matching (comparing repo signals against known skill patterns from `signal-catalog.md`). Each candidate must pass a validation gate requiring at least 3 of 4 extraction criteria. This gate is a repo-level heuristic filter, not a universal law of skill design:
- **Recurrence** -- the pattern appears multiple times
- **Verification** -- success/failure can be objectively checked
- **Non-obviousness** -- the steps are not trivially derivable from file names
- **Generalizability** -- the skill would work across similar repositories

**4C: Agent Candidates.** An agent is recommended only when a concern has BOTH its own toolchain (distinct tools needed) AND its own evaluation criteria (separate success metrics). This is a deliberately conservative repo policy to avoid over-engineering.

**4D: Hook/Rule Candidates.** The decision between hook and rule follows an evidence-informed heuristic: if the check can be expressed as a single command with a boolean pass/fail result, it should be a hook. If judgment is needed to evaluate the result, it should be a rule.

### Phase 5 -- Needs Matrix and Report

**Step 1: Assemble intervention matrix.** Combines all findings into a structured matrix. Each row contains: error class (from taxonomy), gap description, recommended primitive type, priority (P0/P1/P2), estimated token impact, evidence class (canonical vocabulary), confidence, signal source (which analysis step produced the evidence), and concrete evidence (file paths, metrics, or patterns observed).

**Step 2: Optional web validation.** If `websearch_available` is true, the skill runs WebSearch queries to validate the top 3 P0 recommendations against best practices for the detected tech stack. This adds confidence to recommendations but is not required -- the skill degrades gracefully without web access.

**Step 3: Build report.** The report includes YAML frontmatter (following `audit-report-schema.md`) and a body with five sections: Repository Profile (basic stats and existing infrastructure), Static Analysis Summary (key findings from Phase 2), Token Efficiency Summary (key findings from Phase 3), Intervention Matrix (the full prioritized table), and Recommendations grouped by priority (P0, P1, P2).

**Step 4: Present and persist.** The full report is presented to the user, then persisted to `.claude/reviews/YYYY-MM-DDTHHMMSS-audit-repo.md`.

**Step 5: "What's next?" menu.**

1. Scaffold a recommended skill -- `/scaffold-skill`
2. Run deeper skill gap analysis -- `/suggest-skills`
3. Apply audit findings -- `/apply-audit-findings`
4. Done

## Research Behavior

Web research is optional and limited to Phase 5, Step 2. If WebSearch is available, the skill validates the top 3 P0 recommendations by searching for best practices specific to the detected tech stack. If WebFetch is also available, it may fetch 1-2 relevant articles for deeper validation. The skill functions fully without web access -- all core analysis uses local file scanning only.

## Reference Files

| File | Location | Purpose |
|------|----------|---------|
| `references/signal-patterns.md` | Own skill directory | File patterns to scan per analysis step |
| `references/error-class-taxonomy.md` | Own skill directory | Error classes and primitive mapping |
| `references/primitive-decision-matrix.md` | Own skill directory | Decision rules for primitive type selection |
| `references/token-heuristics.md` | Own skill directory | Thresholds and scoring formulas |
| `references/audit-report-schema.md` | Own skill directory | Report frontmatter and body structure |
| `references/signal-catalog.md` | `suggest-skills/references/` (sibling) | Signal tables for skill gap detection |

## Interactions

| Direction | Target | Notes |
|-----------|--------|-------|
| Called by | User directly | Standalone invocation only |
| Calls | Nothing | Diagnostic only -- does not invoke other skills |
| Shares references with | `suggest-skills` | Uses `signal-catalog.md` from suggest-skills |
| Recommends via menu | `/scaffold-skill` | To create primitives from recommendations |
| Recommends via menu | `/suggest-skills` | For deeper skill gap analysis |
| Recommends via menu | `/apply-audit-findings` | To apply the audit recommendations |

## Hard Rules

1. **Read-only on the target repository.** Never modify any file in the analyzed repo. Write only the audit report to `.claude/reviews/`.
2. **Bash only in sub-agents.** Bash is allowed in the Repo Scanner and Token Analyzer agents but not at the top-level skill scope.
3. **Scan limits enforced.** 50 lines per file, 4 directory levels deep, 500 files per directory listing, read-only Bash commands only.
4. **Every recommendation needs evidence.** Each row in the intervention matrix must cite concrete file paths, metrics, or patterns observed during the scan. No speculative recommendations.
5. **Expose uncertainty honestly.** Every intervention must include `evidence_class` and `confidence`, and heuristic or repo-policy mappings must stay labeled as such.
6. **No generation.** The skill produces a diagnostic matrix only. It does not create CLAUDE.md sections, skills, agents, hooks, or rules. That is the job of apply and scaffold skills.
7. **Present all before follow-up.** The complete report is shown to the user before offering the "What's next?" menu.
