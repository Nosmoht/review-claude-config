---
last_refreshed: 2026-03-26
---

# Systematische Claude Code Optimierung für unbekannte Repositories

## Zielsetzung

Deduktives, evidenzbasiertes Verfahren zur Analyse eines beliebigen Repositories und Ableitung aller notwendigen Claude Code Primitives (CLAUDE.md, Skills, Agents, Rules/Hooks) — optimiert auf Korrektheit und Token-Effizienz.

---

## Grundannahmen

- Claude Code Fehler sind nicht zufällig, sondern fallen in vorhersagbare Klassen mit diagnostizierbaren Ursachen im Repo.
- Jede Fehlerklasse mappt auf ein spezifisches Claude Code Primitive (CLAUDE.md, Skill, Agent, Hook/Rule).
- Token-Verbrauch hat eigene, von der Repo-Struktur ableitbare Treiber.
- Frontier-Thinking-LLMs befolgen ca. 150–200 Instruktionen konsistent. Das Claude Code System-Prompt belegt davon bereits ~50. Das effektive Instruktions-Budget liegt bei ~100–150.

---

## Analyse-Framework

Das Framework operiert auf zwei orthogonalen Dimensionen:

| Dimension     | Fragestellung                                     | Output                     |
| ------------- | ------------------------------------------------- | -------------------------- |
| Korrektheit   | Was versteht Claude ohne Hilfe falsch?            | Fehlerklassen → Primitives |
| Effizienz     | Wo verbrennt Claude unnötig Tokens?               | Token-Treiber → Interventions |

---

## Phase 1: Statische Repo-Analyse

Alle Schritte sind **vor dem ersten Claude Code Aufruf** durchführbar. Kein Trial-and-Error nötig.

### 1.1 Toolchain-Detektion

**Ziel**: Deterministische Extraktion aller Build/Test/Lint/Deploy-Kommandos.

**Datenquellen**:

- `package.json` (scripts-Sektion)
- `Makefile` / `Justfile` / `Taskfile.yml`
- `pyproject.toml` / `setup.cfg` / `tox.ini`
- `Dockerfile` / `docker-compose.yml`
- `.github/workflows/*.yml` / `.gitlab-ci.yml` / `Jenkinsfile`
- `Cargo.toml` / `go.mod` / `build.gradle` / `pom.xml`

**Output**: Explizite Kommandoliste (Build, Test einzeln, Test Suite, Lint, Format, Deploy).

**Fehlerklasse**: Toolchain-Fehler (Claude rät Build-Kommandos → Fehlversuche → Token-Verschwendung).

**Primitive**: CLAUDE.md (P0 — höchster Hebel, geringster Aufwand).

### 1.2 Ambiguitäts-Messung

**Ziel**: Navigationskomplexität und Naming-Collisions quantifizieren.

**Metriken**:

- Verzeichnistiefe (max, avg) — >4 Ebenen = exponentiell mehr Navigation
- Dateien pro Verzeichnis (max) — >30 = Grep-Sprawl wahrscheinlich
- Naming-Collision-Score: Identische Klassen-/Funktionsnamen in verschiedenen Packages
- Barrel-/Index-File-Abdeckung (Re-Export-Bündelung vorhanden?)

**Diagnose-Kommandos**:

```bash
# Verzeichnistiefe
find . -type f -not -path './.git/*' | awk -F/ '{print NF-1}' | sort -rn | head -1

# Dateien pro Verzeichnis
find . -type d -not -path './.git/*' -exec sh -c 'echo "$(ls -1 "$1" | wc -l) $1"' _ {} \; | sort -rn | head -10

# Naming-Collisions (TypeScript Beispiel)
grep -rn "export class\|export function\|export const" --include='*.ts' | \
  awk -F'[ (]' '{print $NF}' | sort | uniq -c | sort -rn | head -20
```

**Fehlerklasse**: Navigationsfehler (Claude öffnet falsche Dateien, sucht in falschen Verzeichnissen).

**Primitive**: CLAUDE.md Architektur-Map, aber nur für ambige Pfade.

### 1.3 Linter/Formatter-Coverage-Audit

**Ziel**: Bestimmen welche Konventionen bereits tool-enforced sind und welche Claude explizit gesagt werden müssen.

**Datenquellen**:

- `.eslintrc` / `eslint.config.js` / `biome.json`
- `.prettierrc` / `.editorconfig`
- `ruff.toml` / `pyproject.toml [tool.ruff]` / `mypy.ini`
- `rustfmt.toml` / `.clang-format`
- Pre-Commit-Hooks: `.pre-commit-config.yaml` / `.husky/`

**Entscheidungslogik**:

- Konvention durch Linter/Formatter abgedeckt → **Keine Instruktion nötig** (Claude kann Tool laufen lassen)
- Konvention durch Linter abgedeckt, aber kein Auto-Fix → **Hook-Kandidat** (PostToolUse)
- Konvention existiert nur implizit im Code → **CLAUDE.md Instruktion nötig**

**Fehlerklasse**: Konventionsverletzungen.

**Primitive**: Hook (für tool-enforceable) oder CLAUDE.md (für implizite Konventionen).

### 1.4 Architektur-Pattern-Extraktion

**Ziel**: Implizite Architektur-Entscheidungen erkennen, die Claude nicht aus einzelnen Dateien ableiten kann.

**Indikatoren**:

- Verzeichnisnamen: `adapters/`, `ports/`, `domain/`, `infrastructure/` → Hexagonal
- DI-Framework-Präsenz: `inversify`, `tsyringe`, `Dagger`, Spring → DI-Container
- Schichttrennung: `controller/`, `service/`, `repository/` → Layered Architecture
- Event-Sourcing: `events/`, `commands/`, `projections/` → CQRS/ES
- Existierende ADRs (Architecture Decision Records): `docs/adr/`, `docs/decisions/`

**Diagnose**:

```bash
# Import-Graph-Analyse (Richtung der Abhängigkeiten)
# Erkennt Layer-Violations und tatsächliche Architektur-Boundaries
grep -rn "^import\|^from" --include='*.ts' --include='*.py' | \
  awk -F: '{print $1}' | sort | uniq -c | sort -rn

# ADR-Existenz
find . -type f -iname '*.md' | grep -i 'adr\|decision\|architecture'
```

**Fehlerklasse**: Architektur-Missverständnisse (Claude verwendet falsches Pattern, falsche Abstraktionsebene).

**Primitive**: CLAUDE.md (Architektur-Entscheidungen + Verweis auf ADRs).

### 1.5 Domain-Knowledge-Inventar

**Ziel**: Verfügbarkeit von Domain-Dokumentation prüfen. Einzige Klasse die nicht rein aus Code ableitbar ist.

**Datenquellen**:

- OpenAPI/Swagger Specs
- Protobuf/GraphQL Schema-Dateien
- `GLOSSARY.md` oder äquivalent
- Domain-Model-Diagramme
- README-Abschnitte zu Business-Kontext

**Fehlerklasse**: Domain-Knowledge-Gaps (falsche Begriffe, falsche Business-Logik-Annahmen).

**Primitive**: CLAUDE.md (Verweis auf Domain-Docs oder Glossar).

---

## Phase 2: Token-Effizienz-Analyse

Ergänzt Phase 1 um die Effizienz-Dimension. Ebenfalls statisch durchführbar.

### 2.1 Dateigrößen-Distribution

**Ziel**: Token-Senken identifizieren (Dateien die Claude wahrscheinlich liest und die unverhältnismäßig viele Tokens kosten).

```bash
find . -name '*.ts' -o -name '*.py' -o -name '*.go' -o -name '*.rs' -o -name '*.java' | \
  xargs wc -l | sort -rn | head -20
```

**Schwellwerte**:

- \>500 Zeilen: Token-Senke, Hinweis in CLAUDE.md sinnvoll ("relevante Logik in Zeilen X-Y")
- \>1000 Zeilen: Kritisch, Scope-Eingrenzung oder Refactoring-Empfehlung
- \>2000 Zeilen: ~3000+ Tokens pro Read, aktive Intervention nötig

**Intervention**: CLAUDE.md-Hinweise auf relevante Abschnitte in großen Dateien.

### 2.2 Navigations-Sprawl-Risiko

**Ziel**: Abschätzen wie viele Tool-Calls Claude braucht, um relevante Dateien zu finden.

**Berechnung**: Verzeichnistiefe × Dateien pro Verzeichnis × Naming-Collision-Score

- Score > Schwellwert → Architektur-Map mit Entry Points pro Feature/Domain in CLAUDE.md
- Score niedrig → Keine Navigation-Intervention nötig

### 2.3 Build-Error-Verbosität

**Ziel**: Abschätzen wie teuer Toolchain-Fehlversuche sind.

**Indikatoren**:

- Webpack/Vite/Turbopack → Extrem verbose Errors (oft >500 Zeilen)
- Rust Compiler → Verbose aber informativ
- Go Compiler → Kompakt
- TypeScript `tsc` → Mittel

**Intervention**: Bei verbose Build-Tools expliziten Hinweis in CLAUDE.md: "Build-Errors: relevante Information steht in der ersten Zeile / im `ERROR`-Block."

### 2.4 Monorepo-Scope-Isolation

**Ziel**: Cross-Package-Bleed-Risiko quantifizieren.

**Diagnose**:

```bash
# Wie viele Packages/Workspaces gibt es?
cat package.json | grep -c "workspaces" # Node
find . -name 'go.mod' | wc -l           # Go
find . -name 'Cargo.toml' | wc -l       # Rust

# Wie stark sind sie vernetzt?
# Cross-Package-Import-Score
grep -rn "from '@" --include='*.ts' | grep -v node_modules | \
  awk -F"'" '{print $2}' | sort | uniq -c | sort -rn
```

**Intervention**: Scope-Boundaries in CLAUDE.md: "Wenn du an `packages/X` arbeitest, sind `packages/Y` und `packages/Z` irrelevant."

### 2.5 Context-Burn-Rate-Score

**Ziel**: Abschätzen nach wie vielen Tasks `/compact` oder `/clear` nötig wird.

**Berechnung**: Durchschnittliche Dateigröße (in geschätzten Tokens) × erwartete Reads pro Task-Typ.

**Intervention**: Falls Score hoch → Workflow-Empfehlung für `/compact`-Frequenz als Teil der CLAUDE.md.

---

## Phase 3: Primitives-Ableitung

### 3.1 Skill-Kandidaten — aus Repetitions-Analyse

**Diagnose**: Datei-Similarity-Clustering im Repo.

**Indikatoren**:

- n > Schwellwert gleichförmige Dateien (Components, Services, Handlers, Migrations) → Scaffolding-Skill
- Mehrstufige Workflows in CI → Lokaler Workflow-Skill
- Existierende Codegen-Templates (plop, hygen, cookiecutter) → Wrapper-Skill

**Analyse**:

```bash
# Structural Similarity Detection (Beispiel: React Components)
# Zähle Dateien mit identischem Import-Header-Pattern
find src -name '*.tsx' -exec head -10 {} \; | sort | uniq -c | sort -rn

# Existierende Codegen?
ls -la .plop* .hygen* templates/ generators/ 2>/dev/null
```

**Entscheidungsregel**: Skill lohnt sich ab ≥5 gleichförmigen Dateien mit klar identifizierbarem Skeleton und variablen Teilen.

### 3.2 Agent-Kandidaten — aus Concern-Topologie

**Diagnose**: Import-Graph und CI-Pipeline-Stages verraten Concern-Boundaries.

**Indikatoren**:

- Separate Lint/Test-Configs pro Subdirectory → Spezialisierter Agent pro Domain
- Security-Scanning in CI (Trivy, Snyk, CodeQL) → `security-reviewer` Agent
- Separate Deployment-Targets (Terraform, Helm, CDK) → `infra-architect` Agent
- API-Contract-Validation (OpenAPI, Protobuf) → `api-reviewer` Agent
- CODEOWNERS-Datei mit klaren Verantwortungsbereichen → Agent-Boundaries

**Analyse**:

```bash
# CI-Stage-Analyse
grep -E "stage:|job:|name:" .gitlab-ci.yml .github/workflows/*.yml 2>/dev/null

# Separate Configs pro Subdirectory
find . -name '.eslintrc*' -o -name 'tsconfig*.json' -o -name 'ruff.toml' | \
  awk -F/ '{NF--; print}' OFS=/ | sort | uniq

# CODEOWNERS
cat .github/CODEOWNERS CODEOWNERS docs/CODEOWNERS 2>/dev/null
```

**Entscheidungsregel**: Agent lohnt sich nur wenn der Concern eine **eigene Toolchain UND eigene Bewertungskriterien** hat. Sonst reicht ein Skill.

### 3.3 Rules/Hooks — aus Constraint-Extraktion

**Diagnose**: Bestehende Constraints aus dem Repo extrahieren und als Claude Code Hooks abbilden.

**Datenquellen → Hook-Typ**:

| Quelle                    | Claude Code Primitive          |
| ------------------------- | ------------------------------ |
| Pre-Commit-Hooks          | PostToolUse Hook (Formatter)   |
| Branch-Protection-Rules   | Rule ("Nie auf main committen")|
| Secret-Scanning in CI     | PreToolUse Hook (Secret-Check) |
| .gitignore / .dockerignore| File-Write-Restrictions        |
| Mandatory Review-Labels   | Permission-Config              |
| Dependency-Policies       | PreToolUse Hook (Dep-Check)    |

**Analyse**:

```bash
# Pre-Commit-Hooks
cat .pre-commit-config.yaml .husky/pre-commit 2>/dev/null

# Branch-Protection (nur aus CI/Docs ableitbar, nicht direkt aus Repo)
grep -r "protected_branches\|branch_protection\|require_approval" \
  .gitlab-ci.yml .github/ 2>/dev/null

# Secret-Scanning
grep -r "trivy\|snyk\|gitleaks\|detect-secrets" \
  .pre-commit-config.yaml .github/workflows/ .gitlab-ci.yml 2>/dev/null
```

---

## Phase 4: Bedarfsmatrix generieren

Alle Analyseergebnisse konvergieren in einer priorisierten Matrix:

```
| Fehlerklasse / Treiber   | Gap                      | Primitive  | Prio | Token-Impact |
|---------------------------|--------------------------|------------|------|--------------|
| Toolchain                 | Build-Cmd nicht explizit  | CLAUDE.md  | P0   | High         |
| Toolchain                 | Verbose Build-Errors      | CLAUDE.md  | P0   | High         |
| Navigation                | Monorepo-Ambiguität       | CLAUDE.md  | P0   | High         |
| Navigation                | Große Dateien (>500 LOC)  | CLAUDE.md  | P1   | Medium       |
| Konvention                | Kein Formatter-Hook       | Hook       | P1   | Low          |
| Konvention                | Implizite Patterns        | CLAUDE.md  | P1   | Low          |
| Repetition                | 40 gleichförmige Comps    | Skill      | P1   | Medium       |
| Architektur               | Hexagonal nicht erkennbar | CLAUDE.md  | P1   | Low          |
| Security                  | Trivy/Snyk in CI          | Hook+Agent | P1   | Low          |
| Concern-Separation        | FE/BE eigene Toolchains   | Agent      | P2   | Medium       |
| Domain                    | Kein Glossar vorhanden    | CLAUDE.md  | P2   | Low          |
| Scope-Isolation            | Cross-Package-Bleed       | CLAUDE.md  | P2   | High         |
```

### Priorisierungs-Prinzip

1. **P0 — CLAUDE.md Basics**: Toolchain-Kommandos, Architektur-Map. Höchster Hebel für Korrektheit UND Effizienz.
2. **P1 — Hooks + Skills**: Automatisierbare Guardrails und wiederholbare Patterns.
3. **P2 — Agents + Domain**: Höchster Aufwand, nur bei klarer Concern-Separation oder fehlendem Domain-Kontext.

---

## Phase 5: Generierung

Basierend auf der Bedarfsmatrix werden die Primitives generiert:

### 5.1 CLAUDE.md Generierung

- Starte mit `/init` als Baseline
- Ergänze nur die identifizierten Gaps
- Halte unter 200 Zeilen
- Verwende Progressive Disclosure: Verweise auf Detail-Docs statt Inline-Dokumentation
- Hierarchische Struktur bei Monorepos: Root-CLAUDE.md + Subdirectory-CLAUDE.md

### 5.2 Skill-Generierung

Pro identifiziertem Skill-Kandidat:

- Extrahiere Skeleton aus dem Datei-Cluster
- Identifiziere variable Parameter
- Erstelle SKILL.md mit Template und Parameterbeschreibung
- Ablage in `.claude/skills/`

### 5.3 Agent-Generierung

Pro identifiziertem Agent-Kandidat:

- Definiere Scope (welche Verzeichnisse/Dateien)
- Definiere Toolchain (welche Kommandos)
- Definiere Bewertungskriterien (was ist "korrekt" für diesen Concern)
- Ablage in `.claude/agents/`

### 5.4 Hook/Rule-Generierung

Pro identifiziertem Constraint:

- Mappe auf Hook-Typ (PreToolUse / PostToolUse / Stop)
- Implementiere als ausführbares Script
- Ablage in `.claude/hooks/`

---

## Phase 6: Validierung (einzige empirische Phase)

Nach Generierung aller Primitives: **gezielte Validierung** mit standardisierten Test-Prompts.

### Test-Prompts pro Fehlerklasse

| Fehlerklasse  | Test-Prompt                                          |
| ------------- | ---------------------------------------------------- |
| Toolchain     | "Baue das Projekt und führe die Tests aus"           |
| Navigation    | "Finde die Implementierung von [ambiger Name]"       |
| Konvention    | "Erstelle eine neue Datei vom Typ [häufiger Typ]"    |
| Architektur   | "Füge ein neues Feature nach bestehendem Pattern ein" |
| Domain        | "Erkläre was [Domain-Begriff] im Kontext tut"        |

### Messbare Metriken

- Tool-Calls pro Task (Proxy für Token-Verbrauch)
- Korrektheit (binär: hat das Ergebnis funktioniert)
- Fehlversuche (Anzahl Retry-Zyklen)
- Context-Verbrauch (falls messbar)

### Iterationskriterium

Nur iterieren wenn die Validierung eine **spezifische Lücke** aufdeckt, die in Phase 1–4 nicht identifiziert wurde. Das ist der Unterschied zu Trial-and-Error: die Iteration ist hypothesis-driven, nicht explorativ.

---

## Zusammenfassung

```
Phase 1: Statische Repo-Analyse      → Fehlerklassen + Gaps identifizieren
Phase 2: Token-Effizienz-Analyse     → Verbrauchstreiber quantifizieren
Phase 3: Primitives-Ableitung        → Skills, Agents, Hooks aus Repo-Struktur deduzieren
Phase 4: Bedarfsmatrix               → Priorisierte Interventionsliste
Phase 5: Generierung                 → CLAUDE.md, Skills, Agents, Hooks erstellen
Phase 6: Validierung                 → Gezielter Probelauf, hypothesis-driven Iteration
```

Das Verfahren ist deduktiv: Die Repo-Struktur determiniert die Interventionen. Empirisch ist nur die abschließende Validierung, und auch die ist gezielt statt explorativ.
