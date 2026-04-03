---
name: signal-catalog
description: Baseline signal patterns for detecting missing skill opportunities — deterministic Layer 1 signals plus repo-level decision aids
---

# Signal Catalog

This catalog is the **deterministic baseline** (Layer 1). It catches known patterns reliably. Layer 2 (open reasoning) catches everything else — opportunities that no static table can anticipate. The catalog itself is a repo-maintained decision aid, not a canonical scientific taxonomy of skill gaps.

## Repository Type Classification

Before applying signals, classify the repository:
- **Application**: Has source code (package.json, go.mod, etc.), CI/CD, build tools. Use Application Signal Table.
- **Skills/Config**: Primarily `.claude/skills/`, `research/`, reference material. No source code markers. Use Skills Repository Signal Table.
- **Mixed**: Both source code AND ≥2 skills. Apply both tables.

## Application Signal Table

| Signal | File Pattern | Skill Opportunity | Min Strength |
|--------|-------------|-------------------|-------------|
| Repeated CLAUDE.md workflow | "always", "before X do Y", numbered steps in CLAUDE.md | Extract workflow as dedicated skill | Strong |
| Multi-step rules file | `.claude/rules/*.md` with >3 sequential steps | Elevate rule to full skill with references | Moderate |
| CI workflow complexity | `.github/workflows/*.yml` with >50 lines or 5+ steps | CI helper/debug skill | Moderate |
| Docker + compose | `Dockerfile` + `docker-compose.yml` present | Container management skill | Moderate |
| Test config without test skill | `jest.config*`, `pytest.ini` etc. but no test-related skill | Test orchestration skill | Strong |
| IaC files | `*.tf`, `kustomization.yaml`, `helm/Chart.yaml` | IaC validation/planning skill | Strong |
| Deploy scripts | `scripts/deploy*`, `scripts/release*` | Deployment skill | Strong |
| PR template | `.github/pull_request_template.md` | PR review skill | Moderate |
| Monorepo markers | `lerna.json`, `pnpm-workspace.yaml`, `nx.json` | Cross-package orchestration skill | Strong |
| Build targets >5 | `Makefile`/`Justfile` with >5 targets | Build orchestration skill | Weak |
| Database migrations | `migrations/`, `alembic/`, `prisma/migrations/` | Migration validation skill | Strong |
| API spec files | `openapi.yaml`, `swagger.json`, `*.graphql` | API development skill | Moderate |

## Skills Repository Signal Table

For repositories where `.claude/skills/` is the primary content:

| Signal | Detection Pattern | Skill Opportunity | Min Strength |
|--------|------------------|-------------------|-------------|
| Multiple skills, no review/audit skill | ≥2 skills but none with "review", "audit", "quality" in description | Quality audit skill | Strong |
| References without refresh mechanism | `references/*.md` with dates but no skill manages staleness | Reference refresh skill | Strong |
| Skills share infrastructure without docs | Multiple skills read from same `references/` dir | Shared infrastructure documentation skill | Moderate |
| Review reports without trend analysis | `.claude/reviews/` has ≥3 reports but no analysis skill | Review analytics / portfolio health skill | Moderate |
| Skills with web research but no cache | Skills use WebSearch but no `domain-cache/` exists | Domain cache infrastructure skill | Strong |
| CLAUDE.md workflows not formalized | CLAUDE.md has multi-step processes not covered by any skill | Extract workflow as dedicated skill | Strong |
| No skill creation/scaffolding tool | ≥3 skills but no skill for creating new skills | Skill scaffolding skill | Moderate |
| Skills without cross-skill dependency map | Skills reference each other (read sibling `references/`) but relationships aren't documented | Dependency documentation or validation skill | Weak |
| Research files without index | `research/` dir has ≥5 files but no generated index | Research index/discovery skill | Weak |

## Strength Classification

These strength labels are repo-level signal heuristics for prioritization, not external evidence classes.

- **Strong**: Signal appears in 2+ categories OR represents a high-risk workflow (deploy, migrations, IaC)
- **Moderate**: Single clear signal with well-defined workflow boundaries
- **Weak**: Single signal with ambiguous workflow scope — requires corroboration

## Extraction Criteria

Every suggestion must pass at least 3 of these 4 criteria ([source](https://arxiv.org/html/2603.11808v1)):

| Criterion | Pass | Fail |
|-----------|------|------|
| **Recurrence** | Pattern appears in 2+ files/contexts | One-off occurrence only |
| **Verification** | Workflow expressible as 5-10 clear steps | Too vague to define steps |
| **Non-obviousness** | Requires domain expertise or multi-step logic | Single command or trivial alias |
| **Generalizability** | Works across different inputs/projects | Hardcoded to one specific case |

## Complexity Threshold

Do NOT suggest skills for:
- Single-command operations (e.g., "run prettier", "npm test")
- Simple aliases that add no decision logic
- Workflows with fewer than 3 distinct steps

The exact 3-of-4 gate and complexity cutoffs are `Repo default` filtering rules for this repository.
