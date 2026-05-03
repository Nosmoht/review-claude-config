---
name: signal-catalog
description: Baseline signal patterns for detecting missing skill opportunities — deterministic Layer 1 signals plus repo-level decision aids
last_refreshed: 2026-04-03
---

# Signal Catalog

**S**=Strong **M**=Moderate **W**=Weak (strength labels are repo heuristics, not external evidence classes)

## Repository Type Classification

- **Application**: package.json, go.mod, CI/CD, build tools → Application Signal Table
- **Skills/Config**: `.claude/skills/` is primary content, no source code markers → Skills Repository Signal Table
- **Mixed**: both → apply both tables

## Application Signal Table

| Signal | Pattern | Skill Opportunity | S |
|--------|---------|-------------------|---|
| Repeated CLAUDE.md workflow | "always"/"before X do Y"/numbered steps in CLAUDE.md | Extract as skill | S |
| Multi-step rules file | `.claude/rules/*.md` >3 sequential steps | Elevate to skill | M |
| CI workflow complexity | `.github/workflows/*.yml` >50 lines or 5+ steps | CI debug skill | M |
| Docker + compose | `Dockerfile` + `docker-compose.yml` | Container skill | M |
| Test config without test skill | `jest.config*`, `pytest.ini` — no test skill exists | Test skill | S |
| IaC files | `*.tf`, `kustomization.yaml`, `helm/Chart.yaml` | IaC skill | S |
| Deploy scripts | `scripts/deploy*`, `scripts/release*` | Deploy skill | S |
| PR template | `.github/pull_request_template.md` | PR review skill | M |
| Monorepo markers | `lerna.json`, `pnpm-workspace.yaml`, `nx.json` | Cross-package skill | S |
| Build targets >5 | `Makefile`/`Justfile` >5 targets | Build skill | W |
| Database migrations | `migrations/`, `alembic/`, `prisma/migrations/` | Migration skill | S |
| API spec files | `openapi.yaml`, `swagger.json`, `*.graphql` | API skill | M |

## Skills Repository Signal Table

| Signal | Detection Pattern | Skill Opportunity | S |
|--------|-----------------|-------------------|---|
| Multiple skills, no review/audit | ≥2 skills, none with review/audit/quality in description | Quality audit skill | S |
| References without refresh | `references/*.md` with dates, no refresh skill | Reference refresh skill | S |
| Skills share infrastructure | Multiple skills read same `references/` dir | Shared infra docs skill | M |
| Review reports, no analytics | `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` ≥3 reports, no analytics skill | Review analytics skill | M |
| Web research, no cache | Skills use WebSearch, no `domain-cache/` | Domain cache skill | S |
| CLAUDE.md workflows not formalized | Multi-step CLAUDE.md processes with no covering skill | Extract as skill | S |
| No scaffolding tool | ≥3 skills, no skill-creation skill | Scaffolding skill | M |
| No cross-skill dependency map | Skills cross-read sibling `references/`, undocumented | Dependency skill | W |
| Research files without index | `research/` ≥5 files, no generated index | Research index skill | W |

## Agent Candidate Signal Table

| Signal | Detection Pattern | Agent Candidate | S |
|--------|-------------------|-----------------|---|
| Security scanning toolchain | `.github/workflows/*.{yml,yaml}` references Trivy / Snyk / CodeQL / gitleaks AND no `agents/security*` exists | `security-reviewer` agent | S |
| Separate IaC deployment targets | ≥2 of `*.tf`, `helm/Chart.yaml`, `cdk.json`, `kustomization.yaml` AND no `agents/infra*` exists | `infra-architect` agent | S |
| Database-migration toolchain isolated | `migrations/`, `alembic/`, or `prisma/migrations/` AND no `agents/migration*` exists | `migration-reviewer` agent | S |
| Release-engineering toolchain isolated | `scripts/release*` + `.github/workflows/release*.yml` use a toolchain absent from `make test` | `release-engineer` agent | W |

## Rule Candidate Signal Table

| Signal | Detection Pattern | Rule Candidate | S |
|--------|-------------------|----------------|---|
| Branch-protection enforcement on `main` | `.github/branch_protection.json` OR repo policy prohibits direct push to `main`/`master` | `no-direct-push-to-main` rule | S |
| Review-label routing requiring judgment | repo workflow requires PR labels (`needs: security-review`, `needs: arch-review`) selected by content judgment | `pr-review-label-routing` rule | M |
| Sensitive-path write-restriction | `.gitignore`/`.dockerignore` patterns where exclusion rationale is non-mechanical (e.g., `secrets/`, `*.local.*`) | `sensitive-paths-write-restriction` rule | M |
| Commit-message style requiring narrative judgment | `CONTRIBUTING.md` / `STYLE.md` clauses like "prefer X unless Y" — not single-command checkable | `commit-message-style` rule | M |

## Extraction Criteria

Every suggestion must pass 3/4 ([source](https://arxiv.org/html/2603.11808v1)):
- **Recurrence**: 2+ files/contexts (fail: one-off)
- **Verification**: expressible as 5-10 steps (fail: too vague)
- **Non-obviousness**: requires domain expertise or multi-step logic (fail: single command or trivial alias)
- **Generalizability**: works across inputs/projects (fail: hardcoded to one case)

Do NOT suggest: single-command ops, trivial aliases, <3 distinct steps. The 3/4 gate and cutoffs are `Repo default`.
