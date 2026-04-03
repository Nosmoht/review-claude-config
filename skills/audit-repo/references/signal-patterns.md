---
name: signal-patterns
description: File patterns and Glob/Grep queries for each audit analysis step
---

## Toolchain Detection

| Signal | Pattern | Extract |
|--------|---------|---------|
| Package scripts | `package.json` | `scripts` section |
| Build targets | `Makefile`, `Justfile`, `Taskfile.yml` | target names |
| Python config | `pyproject.toml`, `setup.cfg`, `tox.ini` | scripts/commands |
| Containers | `Dockerfile`, `docker-compose.yml` | build/run commands |
| CI pipelines | `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile` | step commands |
| Rust | `Cargo.toml` | `cargo` commands |
| Go | `go.mod` | `go build/test` |
| Java | `build.gradle`, `pom.xml` | tasks/goals |

## Convention Enforcement

| Tier | Detection Files |
|------|----------------|
| Deterministic | `.eslintrc*`, `biome.json`, `ruff.toml`, `.prettierrc*`, `rustfmt.toml`, `.editorconfig` |
| CI-enforced | `.github/workflows/*.yml` steps running lint/format |
| AI-instructed | `CLAUDE.md`, `.claude/rules/*.md`, `.cursorrules`, `.github/copilot-instructions.md` |
| Undocumented | (inferred from code patterns only) |

## Architecture Signatures

| Pattern | Directory Names |
|---------|----------------|
| Hexagonal | `adapters/`, `ports/`, `domain/`, `infrastructure/`, `core/` |
| MVC | `models/`, `views/`, `controllers/`, `routes/`, `templates/` |
| Layered | `controller/`, `service/`, `repository/`, `presentation/`, `business/`, `data/` |
| Clean | `entities/`, `usecases/`, `interfaces/`, `frameworks/` |
| Microservices | multiple `Dockerfile` per service, separate `go.mod`/`package.json` |

## Domain Knowledge and Monorepo Markers

**Domain:** `openapi.yaml`, `swagger.json`, `*.proto`, `*.graphql`, `schema.graphql`, `GLOSSARY.md`, `docs/adr/`, `docs/decisions/`, `migrations/`, `prisma/schema.prisma`, `*.dbml`, `*.avsc`

**Monorepo:** `lerna.json`, `pnpm-workspace.yaml`, `nx.json`, `turbo.json`, package.json `workspaces`, multiple `go.mod`/`Cargo.toml`
