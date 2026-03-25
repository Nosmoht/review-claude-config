# Repo Readiness Frameworks for AI Coding Assistants

Sources:
- [Factory.ai Agent Readiness](https://factory.ai/news/agent-readiness) — 8 pillars, 5 maturity levels; commercial framework measuring how well a repo supports autonomous development
- [Factory.ai Agent Readiness Docs](https://docs.factory.ai/web/agent-readiness/overview) — Official documentation with pillar definitions and level criteria
- [Kodustech agent-readiness](https://github.com/kodustech/agent-readiness) — Open-source alternative to Factory.ai; 7 pillars, 39 automated checks, 10+ languages
- [AgentReady by ambient-code](https://github.com/ambient-code/agentready) — 50+ source-backed attributes, 13 assessment categories, certification tiers (Platinum/Gold/Silver/Bronze)
- [ContextPilot](https://github.com/contextpilot-dev/contextpilot) — Auto-detects frameworks from config files, generates .cursorrules/CLAUDE.md/copilot-instructions.md

Fetched: 2026-03-26

## Framework Comparison

Three tools evaluate how ready a repository is for AI coding agents. They share the same premise — the agent is not broken, the environment is — but differ in scope and approach.

**Factory.ai Agent Readiness** (commercial, closed-source):
- 8 pillars: Style & Validation, Build System, Testing, Documentation, Dev Environment, Code Quality, Observability, Security & Governance
- 5 maturity levels (must pass 80% of criteria at each level to advance); Level 3 is the recommended target for most teams
- Integrated into Factory CLI (`/readiness` slash command) and web dashboard
- Examples: CockroachDB scores Level 4; Express scores Level 2

**Kodustech agent-readiness** (open-source, MIT):
- 7 pillars: Style & Linting, Testing, Documentation, Dev Environment, CI/CD, Code Health, Security
- 39 automated checks across 10+ languages; same 80%-to-advance maturity model
- Runnable standalone: `bunx @kodus/agent-readiness .`
- Drops Factory's Observability pillar; adds CI/CD as a distinct pillar

**AgentReady by ambient-code** (open-source):
- 13 assessment categories with 50+ attributes; each attribute backed by peer-reviewed or authoritative sources (Anthropic, Microsoft, Google, ArXiv, IEEE/ACM)
- Certification tiers: Platinum, Gold, Silver, Bronze (based on attribute pass rates)
- Generates interactive HTML and version-control-friendly Markdown reports with actionable remediation steps
- More granular than pillar-based models; trades simplicity for attribution depth

| Dimension | Factory.ai | Kodustech | AgentReady |
|-----------|-----------|-----------|------------|
| Pillars/Categories | 8 | 7 | 13 |
| Checks | undisclosed | 39 | 50+ attributes |
| Maturity model | 5 levels | 5 levels (mirrored) | 4 certification tiers |
| Open source | No | Yes (MIT) | Yes |
| Runs locally | Via Factory CLI | `bunx` standalone | `pip install` standalone |

## Convention Enforcement Tiers

Repository conventions exist on a spectrum of enforceability. All three frameworks implicitly assess this but none name the tiers explicitly:

1. **Deterministic** — Machine-verified, zero ambiguity. Examples: type checkers (mypy, tsc), formatters (prettier, black), lockfiles (package-lock.json, poetry.lock). An agent can trust these signals absolutely.
2. **CI-enforced** — Verified on every push but may have escape hatches (skip-ci, force-merge). Examples: required CI checks, coverage thresholds, linter gates in GitHub Actions. Agents can trust these if the CI config is readable.
3. **AI-instructed** — Written for agent consumption but not machine-enforced. Examples: CLAUDE.md, .cursorrules, AGENTS.md, CONTRIBUTING.md. Quality depends entirely on maintenance; prone to drift.
4. **Undocumented** — Tribal knowledge that exists only in team members' heads. Invisible to agents. This is where most agent failures originate — the agent makes a reasonable choice that violates an unwritten norm.

Factory.ai and Kodustech primarily detect tiers 1-2 (config file presence, CI setup). AgentReady extends into tier 3 (checks for AI context files). No tool systematically detects tier-4 gaps.

## Config Files as Primary Signals

All frameworks rely on config file detection as the foundation of their analysis. The files agents look for to understand a repo's toolchain:

**Build & Dependencies:** package.json, pyproject.toml, Cargo.toml, go.mod, Makefile, Dockerfile, docker-compose.yml
**Style & Linting:** .eslintrc, .prettierrc, .editorconfig, ruff.toml, .flake8, mypy.ini, tsconfig.json
**Testing:** jest.config.*, vitest.config.*, pytest.ini, .nycrc, codecov.yml
**CI/CD:** .github/workflows/*.yml, .gitlab-ci.yml, Jenkinsfile, .circleci/config.yml
**AI Context:** CLAUDE.md, .cursorrules, copilot-instructions.md, AGENTS.md, .github/copilot-instructions.md
**Security:** .snyk, .trivyignore, CODEOWNERS, SECURITY.md

ContextPilot takes a different approach: rather than scoring, it reads these same config files to auto-generate AI context files. Running `contextpilot init` detects frameworks, ORMs, testing tools, and styling libraries, then produces tool-specific instruction files (.cursorrules, CLAUDE.md, copilot-instructions.md). It also provides an MCP server for native Claude Code integration. The limitation: detection is shallow (framework name + version) with no assessment of how well the toolchain is configured.

## Gap: No Existing Tool Maps Repo to Error Classes to Primitives

The fundamental gap across all four tools: none of them close the loop from **repo state** to **predicted agent failure modes** to **specific primitives that would prevent those failures**.

- Factory.ai / Kodustech detect *what is present* (linter exists, tests exist) but not *what errors agents will make* without specific missing pieces
- AgentReady adds attribution depth (why each attribute matters) but still operates at the attribute level, not the error-prediction level
- ContextPilot is the closest to the right idea — it reads repo signals and produces agent instructions — but its output is generic framework boilerplate, not targeted at the specific error classes that repo's structure would produce

The missing tool would: (1) statically analyze a repo's config files, code patterns, and existing documentation; (2) predict the specific classes of errors an AI agent would make (wrong test runner, missing env vars, incorrect import paths, style violations); (3) generate or recommend the minimal set of primitives (rules, skills, context files) that would prevent those specific errors. This is the repo-to-error-to-primitive pipeline that no existing tool implements end-to-end.
