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
| Review reports, no analytics | `.claude/reviews/` ≥3 reports, no analytics skill | Review analytics skill | M |
| Web research, no cache | Skills use WebSearch, no `domain-cache/` | Domain cache skill | S |
| CLAUDE.md workflows not formalized | Multi-step CLAUDE.md processes with no covering skill | Extract as skill | S |
| No scaffolding tool | ≥3 skills, no skill-creation skill | Scaffolding skill | M |
| No cross-skill dependency map | Skills cross-read sibling `references/`, undocumented | Dependency skill | W |
| Research files without index | `research/` ≥5 files, no generated index | Research index skill | W |

## Extraction Criteria

Every suggestion must pass 3/4 ([source](https://arxiv.org/html/2603.11808v1)):
- **Recurrence**: 2+ files/contexts (fail: one-off)
- **Verification**: expressible as 5-10 steps (fail: too vague)
- **Non-obviousness**: requires domain expertise or multi-step logic (fail: single command or trivial alias)
- **Generalizability**: works across inputs/projects (fail: hardcoded to one case)

Do NOT suggest: single-command ops, trivial aliases, <3 distinct steps. The 3/4 gate and cutoffs are `Repo default`.
