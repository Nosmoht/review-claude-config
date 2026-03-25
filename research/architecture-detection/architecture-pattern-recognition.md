# Architecture Pattern Recognition from Repository Structure

Sources:
- [ArchAgent: Scalable Legacy Software Architecture Recovery with LLMs](https://arxiv.org/abs/2601.13007) — LLM-based agentic architecture recovery combining static analysis, adaptive code segmentation, and cross-repository heuristics
- [dependency-cruiser](https://github.com/sverweij/dependency-cruiser) — JS/TS/CoffeeScript dependency validation and visualization tool with configurable rule sets
- [ArchUnit](https://www.archunit.org/) — Java architecture test library for asserting package/layer dependency rules in unit tests
- [depguard](https://github.com/OpenPeeDeeP/depguard) — Go linter enforcing allowlist/denylist constraints on package imports
- [Codified Context: Infrastructure for AI Agents in a Complex Codebase](https://arxiv.org/abs/2602.20478) — 108K-line C# system with 19 domain-expert agents and 34 specification documents across 283 sessions
- [Domain-Driven Hexagon](https://github.com/Sairyss/domain-driven-hexagon) — Reference implementation of hexagonal architecture with DDD, including canonical directory layout

Fetched: 2026-03-26

## Hybrid Detection Approach

Architecture detection benefits from a two-pass strategy: directory-name heuristics provide fast, high-recall pattern matching, while import/dependency graph analysis adds slower but high-precision validation.

ArchAgent (arxiv:2601.13007) demonstrates this hybrid approach at scale: static analysis extracts dependency graphs, then LLM-powered synthesis classifies architectural patterns. Their ablation study confirms that dependency context significantly improves accuracy over structure-only detection. For skill-gap analysis, a lightweight version applies: scan directory names first to generate candidate patterns, then validate candidates against actual import graphs where tooling is available.

The Codified Context paper (arxiv:2602.20478) reinforces this by showing that a 108K-line C# codebase required 34 on-demand specification documents to capture architecture that could not be inferred from code structure alone. Directory heuristics catch the obvious patterns; dependency analysis and explicit documentation catch the rest.

## Architecture Signature Directories

High-confidence directory-name signals for common architecture patterns:

| Pattern | Signature Directories | Confidence |
|---|---|---|
| Hexagonal / Ports & Adapters | `domain/`, `ports/`, `adapters/`, `infrastructure/` | High if 3+ present |
| MVC | `models/`, `views/`, `controllers/` | High (very common) |
| Clean Architecture | `entities/`, `usecases/` (or `use_cases/`), `interfaces/`, `frameworks/` | High if usecases present |
| CQRS | `commands/`, `queries/`, `events/` | High if all three present |
| Microservices | Multiple `Dockerfile`s, `docker-compose.yml` with multiple services, per-service directories | Medium (needs service boundaries) |
| Layered | `presentation/`, `business/` (or `service/`), `data/` (or `persistence/`) | Medium (generic names) |
| DDD | `aggregates/`, `value_objects/`, `repositories/`, `bounded_contexts/` | High if aggregates present |

False positive mitigation: a single matching directory (e.g., `models/` alone) is insufficient. Require 2+ co-occurring signature directories before asserting a pattern. Microservices detection additionally requires evidence of independent deployment (separate Dockerfiles or CI configurations).

## Dependency Graph Analysis Tools

Static enforcement tools validate that actual imports respect declared architectural boundaries:

**JavaScript/TypeScript: dependency-cruiser** ([github.com/sverweij/dependency-cruiser](https://github.com/sverweij/dependency-cruiser))
- Validates import rules: circular dependency detection, orphan detection, layer violation checks
- Configurable via `.dependency-cruiser.js` with forbidden/allowed patterns
- Supports ES6, CommonJS, AMD; understands TypeScript, Vue SFC, Svelte
- Output formats: JSON, Mermaid, DOT, HTML for visualization

**Java: ArchUnit** ([archunit.org](https://www.archunit.org/))
- Expresses architecture rules as unit tests: `noClasses().that().resideInAPackage("..domain..").should().dependOnClassesThat().resideInAPackage("..infrastructure..")`
- Built-in layered architecture checks, slice isolation, cycle detection
- Runs in standard JUnit 4/5; bytecode-level analysis (no source parsing needed)

**Go: depguard** ([github.com/OpenPeeDeeP/depguard](https://github.com/OpenPeeDeeP/depguard))
- Allowlist/denylist linter for Go package imports
- Integrates with golangci-lint; supports prefix and glob matching
- Enforces module boundary constraints (e.g., `internal/` package conventions)

For skill-gap detection: the presence of these tools' configuration files (`.dependency-cruiser.js`, ArchUnit test classes, `.depguard.json`) signals that a project already codifies architectural boundaries, reducing the need for agent-inferred rules.

## Domain Knowledge Sources

Certain repository artifacts are high-signal indicators of domain complexity that should trigger architecture-aware skill suggestions:

**API Specifications:** OpenAPI/Swagger (`openapi.yaml`, `swagger.json`), Protocol Buffers (`.proto` files), GraphQL schemas (`.graphql`, `schema.graphql`) reveal service boundaries, domain entities, and inter-service contracts.

**Architecture Decision Records (ADRs):** Files in `doc/adr/`, `docs/decisions/`, or `architecture/decisions/` following the Nygard format (MADR or similar) document explicit architectural choices. Their presence indicates a team that values architectural documentation.

**Domain Glossaries:** Files named `GLOSSARY.md`, `ubiquitous-language.md`, or similar in `docs/` signal DDD practices and provide entity/aggregate naming that informs skill boundaries.

**Dependency Lock Files:** `package-lock.json`, `go.sum`, `Cargo.lock`, `poetry.lock` reveal the dependency graph without running build tools. Framework choices (Express vs. Nest, Spring Boot vs. Micronaut) strongly predict architectural patterns.

## Inferable vs Must-Document Conventions

Not all conventions need explicit documentation. Some can be reliably inferred from code; others require human-authored specification.

**Reliably inferable from code patterns:**
- Naming conventions (camelCase vs. snake_case, file naming patterns)
- Test file organization (co-located vs. separate `__tests__/` directories)
- Import style (relative vs. absolute, barrel files)
- Framework and language choices (from dependencies and file extensions)
- Build tool configuration (from config files)

**Must be explicitly documented (not inferable):**
- Architectural boundary rules (which layers may import which)
- Domain concepts and bounded context boundaries
- Deployment topology and service ownership
- Non-obvious conventions (e.g., "handlers must not call repositories directly")
- Performance budgets and SLA constraints
- Security boundaries and trust zones

The Codified Context paper (arxiv:2602.20478) found that their 108K-line system required explicit documentation for architectural boundaries despite having well-organized directory structures. The directory layout hinted at the architecture, but the actual dependency rules, exception cases, and cross-cutting concerns needed codified specification across 34 documents. This finding directly informs skill-gap detection: when directory heuristics detect an architecture pattern but no corresponding constraint documentation exists (ADRs, ArchUnit tests, dependency-cruiser config), that gap is a high-value skill suggestion candidate.
