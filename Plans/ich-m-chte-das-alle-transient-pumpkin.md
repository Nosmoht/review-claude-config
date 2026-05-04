# Right-Altitude-Refactor: alle Verstöße fixen

**Track**: manual (R1–R4 nicht erfüllt für `/implement-issue`-Track; bewusst gewählt).

## Context

Audit gegen `~/workspace/claude-config/rules/right-altitude.md` hat 9 Code-Artefakte
identifiziert, die gegen die "leichteste sufficient form"-Regel verstoßen. Maintainer
entscheidet bewusst was akzeptiert wird; dieser Plan fixt **alle** 9 + zwei Pre-PR-Audit-Schritte
für mögliche zusätzliche Verstöße in `rubric_binary_evaluator.py` und
`perspective_certificate_parser.py` (von Multi-Perspective-Review aufgedeckt).

Hauptmuster: Policy-Tabellen werden als Python-`dict`-Konstanten kodiert statt als
deklarative Daten. Plan überführt sie in YAML/JSON-Files unter erhalt der
Determinismus-Garantien.

## Forschungs-Evidenz (Cat-C-Auflösung)

| Quelle | Tier | Befund |
|---|---|---|
| arXiv 2603.13287 (2026) "From Stochastic Answers to Verifiable Reasoning" | 1 | Drei Failure-Modes von per-instance LLM-Evaluation: Cost-Scaling, Stochastic Instability, Auditability-Gaps. Empfiehlt LLM-als-Code-Generator-Pattern für Decision-Tasks. |
| Anthropic Engineering "Effective Context Engineering" | 1 | **Zwei symmetrische Failure-Modes** (Doppelzitat): (a) "hardcoding complex, brittle logic" (b) "vague, high-level guidance". Mittlere Position empfohlen, nicht Code-Maximierung. |
| `rubric_binary_evaluator.py:2-8` | 2 | "Eliminating ~80% run-to-run variance" — empirische repo-spezifische Messung. Hauptbeleg. |

**Auflösung**: `check_convergence` und `escalation_decision` sind set-operations + boolean-AND + max-min-arithmetic + threshold-checks. Right-Altitude L82-84 erlaubt Code für genau diese Operationen. Cat C → **Cat B**.

## User-Decisions (verbindlich, Runde 1 + Runde 2)

1. **Schema-Validation**: Python `jsonschema`-Lib, kein node/npm. `validate_schema.py` Cat A → **Cat B**.
2. **`bin/`-Konvention**: etabliert mit `shellcheck`-Integration als **hard requirement** in `make lint` (kein graceful-degrade). Erste Anwendung: `bin/sync-marketplace-ref.sh`.
3. **SOT-Strategie**: **C+** — `scoring-rubric.md` ist alleiniger Master, wird in Stufe 0 strukturell erweitert um 3 normative Tabellen-Sektionen für `BINARY_ITEM_IDS`, `BINARY_CAPS` (inkl. F-Caps), `AGENT_ITEM_DIMENSION`. `merge-policy.yaml` wird CI-generiert.
4. **PR-Strategie**: 1 atomarer PR mit Squash-Merge.
5. **`validate_token_budgets.py`**: bleibt Python thin reader (~50 LOC) — Cat A → **Cat B** (Right-Altitude-Konsistenz: bin/*.sh würde >30 LOC und damit auch Code-Stufe sein, ohne empirischen Vorteil).

## Vollständige Liste (finale Kategorisierung)

| # | Pfad | LOC heute | Kat | Ziel-Form | Output |
|---|---|---|---|---|---|
| 1 | `scripts/sync-marketplace-ref.py` | 120 | A | `bin/sync-marketplace-ref.sh` ~25 LOC | bin/ + Makefile-Update |
| 2 | `scripts/validate_schema.py` | 323 | B | thin reader ~80 LOC | 6 JSON-Schemas in references/schemas/ |
| 3 | `scripts/validate_token_budgets.py` | 203 | B | thin reader ~50 LOC | references/token-budgets.json |
| 4 | `scripts/merge_findings.py` | 911 | B | Konstanten raus, ~600 LOC Algo | merge-policy.yaml (CI-generiert) |
| 5 | `scripts/audit_preflight.py` | 155 | B | thin reader ~50 LOC | references/audit-triggers.yaml |
| 6 | `hooks/policy_gate.py` | 257 | B | thin reader ~100 LOC | hooks/policy_gate.json |
| 7 | `hooks/session_check.py` | 179 | B | thin reader ~100 LOC | hooks/session_check.json |
| 8 | `scripts/check_convergence.py` | 168 | B | nur Konstanten als YAML; Predikate als Code | references/convergence-rules.yaml (Konstanten) |
| 9 | `scripts/escalation_decision.py` | 94 | B | nur Konstanten als YAML; Predikate als Code | references/escalation-rules.yaml (Konstanten) |
| **A1** | Audit auf `rubric_binary_evaluator.py` | 1726 | Audit | prüfen 28 Check-Funktionen | Stufe 0; bei Verstoß: User-Approval-Gate |
| **A2** | Audit auf `perspective_certificate_parser.py` | 333 | Audit | markdown-it-py Spike | Stufe 0; bei Verstoß: User-Approval-Gate |

**Hinweis zu hooks/policy.json-Aufteilung**: nach Reviewer-Finding F1 (geteilte Datei = gekoppelte blast radius) wird in **zwei separate Files** aufgeteilt: `hooks/policy_gate.json` + `hooks/session_check.json`. Schema je Datei.

## Aufrufer-Inventar (32 Update-Punkte)

| Skript | Aufrufer (verifiziert) |
|---|---|
| `merge_findings.py` | 6 Tests (16 importierte Symbols) + `check_convergence.py:38-39` Import + `skills/review-skill/SKILL.md:172` |
| `validate_schema.py` | `Makefile:14` + `.github/workflows/ci.yml:39` + `hooks/session_check.py:22` (Hard-Sync-Comment) + 1 Test |
| `validate_token_budgets.py` | `Makefile:17` + 1 Test |
| `check_convergence.py` | `skills/review-skill/SKILL.md:184` + 1 Test |
| `escalation_decision.py` | `skills/review-skill/SKILL.md:176` + 1 Test |
| `sync-marketplace-ref.py` | `Makefile:25` + `.github/workflows/release-please.yml:42` |
| `audit_preflight.py` | 1 Test + 1 Script-Import |
| `policy_gate.py` | `hooks/hooks.json:21` + 45 Tests |
| `session_check.py` | `hooks/hooks.json:85` + 34 Tests |

## Frozen CLI-Contract (4 thin readers)

| Skript | Args | Flags | Exit-Codes |
|---|---|---|---|
| `merge_findings.py` | `<session_dir>` | `--findings-out PATH`, `--repo-root PATH` | 0/non-0 |
| `check_convergence.py` | `<run1.json> <run2.json>` | `--max-variance N` (default 1) | 0/1 |
| `escalation_decision.py` | `<merged-cert.json>` | `[--deep]` | 0=no-escalation, 2=escalate |
| `audit_preflight.py` | — | `[--show-paths]` | 0 |

Snapshot-Test (`tests/test_refactor_byte_identical.py`) diff-pre/post stdout+stderr+exit-code.

## Konventionen für neue Files

- **JSON-Schemas**: `additionalProperties: false`, `$schema: "https://json-schema.org/draft/2020-12/schema"`, `$id`, `title`, `description`. Konvention dokumentiert in `references/schemas/CONVENTIONS.md`.
- **YAML-Policy-Files**: AUTO-GENERATED-Header für derived files (`merge-policy.yaml`); maintainer-edited files (`audit-triggers.yaml`, `convergence-rules.yaml`, `escalation-rules.yaml`, `token-budgets.json`) ohne Header.
- **`bin/*.sh`**: shellcheck-clean, hard-required (CI fails wenn shellcheck fehlt — kein graceful-degrade).
- **`scripts/*.py`** vs **`bin/*.sh`**: CLAUDE.md §Architecture neuer Eintrag dokumentiert: "scripts/ für Python-Skripte und ≥100-LOC-Bash-Skripte mit Pipeline-State (z. B. bestehender `scripts/issue-state.sh`); `bin/` für deterministische Bash-Helper ≤30 LOC. Existing `scripts/issue-state.sh` bleibt unverschoben (legacy-Position dokumentiert)."

## Refactor-Strategie (1 atomarer PR, 5 Stufen)

### Stufe 0 — Pre-flight (separate Vor-Session, eigene Commits)

**Wichtig**: läuft in eigener Session vor Refactor wegen Mid-Session-Freeze (Hard-Constraint #6). **Erzwingung**: Stufe-0-End-Commit ist `chore(session): close pre-flight session`; Stufe 1 darf nur in einer NEUEN Session committet werden. PR-Description hat eine Checkbox "Pre-flight session closed in commit `<SHA>` before refactor session began".

- **0.1 Pre-PR-Audits** (read-only):
  - `rubric_binary_evaluator.py` Audit: dispatchen als Explore-Sub-Agent mit Auftrag "lies alle 28 `check_*()`-Funktionen, klassifiziere jede als (a) deterministisch (regex/string-ops/counting/bool-logic), (b) LLM-binary fallback (z. B. CLAR-2 dokumentiert das als legitim), (c) anders". Output: Markdown-Tabelle nach `Plans/audit-rubric-eval-rightaltitude.md`. Bei (c)-Findings: AskUserQuestion ob in PR aufnehmen oder als follow-up Issue.
  - `perspective_certificate_parser.py` Spike: 30-Min-PoC mit `markdown-it-py` für Haiku-Lenient-Parser-Pfad. Wenn ≤80 LOC + alle 21 Tests grün: AskUserQuestion ob Cat-A-Migration in PR. Sonst: "bewusst akzeptiert" in Plans-Datei.

- **0.2 SOT-Strategie-C+ Setup** — `scoring-rubric.md` strukturell erweitern (~120 LOC neuer Inhalt):
  - Frontmatter-Eintrag `derived-policy: skills/review-skill/references/merge-policy.yaml`
  - Header-Notiz "Items werden CI-generiert nach merge-policy.yaml"
  - Neue Sektion `## Item Inventory` mit pipe-delimited Tabelle aller 32 BINARY_ITEM_IDS + 14 NARRATIVE_PARENT_IDS + 32 ITEM_DIMENSION-Mappings
  - Neue Sektion `## Grade Caps` mit pipe-delimited Tabelle aller 20 BINARY_CAPS-Tupel inkl. F-Caps (z. B. "SAMP-2 → Metadata → F (hard, runtime 400-error)")
  - Neue Sektion `## Agent Items` mit pipe-delimited Tabelle aller 26 AGENT_ITEM_DIMENSION-Mappings (migriert aus `agent-evaluation-guide.md`)
  - `agent-evaluation-guide.md` bekommt Header-Notiz "Dim-Mappings sind in scoring-rubric.md §Agent Items definiert"
  - Diese Edits werden NUR in Stufe 0 (Vor-Session) gemacht; Refactor-Session berührt rubric.md nicht

- **0.3 `bin/`-Konvention etablieren**:
  - `mkdir bin/` + `.gitkeep`
  - `Makefile`: addiere `lint`-Schritt `shellcheck bin/*.sh` (hard-required)
  - `CONTRIBUTING.md` ergänzen mit shellcheck-Prerequisite (Mac: `brew install shellcheck`, Linux: `apt install shellcheck`)
  - `CLAUDE.md §Architecture` neuer Konvention-Eintrag (siehe oben)
  - `tests/test_bin_smoke.py`: smoke-test pro bin-Skript (existiert + executable + shellcheck-clean)

Stufe-0-Commits: ≥4 separate Commits, eigene Session, abgeschlossen via `chore(session): close pre-flight session`.

### Stufe 1 — Cat A: bin/sync-marketplace-ref (1 Commit)

1. **`bin/sync-marketplace-ref.sh` + Makefile + Skript-delete in EINEM Commit**:
   - `bin/sync-marketplace-ref.sh` (~25 LOC, shellcheck-clean): `VERSION=$(jq -r '.version' .claude-plugin/plugin.json)`; SemVer-Validierung mit `grep -E`; `jq` schreibt marketplace.json (Format-Re-Format akzeptiert, CHANGELOG dokumentiert "marketplace.json now uses jq-canonical formatting"); `BREAKING CHANGE:`-Footer für release-please-Major-Bump
   - `Makefile:25` + `.github/workflows/release-please.yml:42`
   - `git rm scripts/sync-marketplace-ref.py`
   - `make validate` grün

### Stufe 2 — Cat B: Policy-Extraktion (5 Commits)

2. **`scripts/regenerate_merge_policy.py` + initial yaml** (Setup-Commit):
   - `scripts/regenerate_merge_policy.py` (~80 LOC, custom Tabellen-Parser auf rubric.md §Item Inventory + §Grade Caps + §Agent Items; markdown-it-py optional aber nicht zwingend, da neue Tabellen einheitlich formatiert)
   - `skills/review-skill/references/merge-policy.yaml` initial-erzeugt + committed (AUTO-GENERATED-Header)
   - Pre-commit-Hook NICHT addiert (User-Decision #3 war "ODER"); stattdessen NUR CI-Workflow
   - `.github/workflows/policy-consistency.yml`: regeneriert yaml aus rubric, fails wenn diff (= "yaml ist nicht-aktuell zu rubric")
   - 1 Test `tests/test_regenerate_merge_policy.py` (Roundtrip-fixtures)
3. **`merge_findings.py` Migration**:
   - Konstanten-Definitionen entfernt
   - **Lazy-Load-Pattern**: `def __getattr__(name): if name in _LAZY_NAMES: return _load_policy()[name]` (PEP 562). Damit ist `import merge_findings` failure-resilient — yaml-Load erst beim First-Access. Bei fehlendem File: `RuntimeError("merge-policy.yaml missing — run scripts/regenerate_merge_policy.py")`.
   - CLI-Interface frozen (Frozen-Contract-Tabelle)
   - Layer-0/1/1.5-Algorithmus bleibt
   - 6 Tests: Module-Level-`__getattr__` ist transparent für `monkeypatch.setattr(merge_findings, "BINARY_ITEM_IDS", …)` — keine Test-Rewrites
   - `check_convergence.py:38-39` Import: bleibt funktional (lazy-load greift)
4. **`hooks/policy_gate.py` Migration**:
   - `hooks/policy_gate.json` (top-level keys: `tool_levels`, `bash_l5_patterns`, `mcp_l1_prefixes`, `mcp_l4_verbs`, `default_policy`, `policy_version: "1.0"`)
   - `references/schemas/policy-gate.schema.json` (additionalProperties: false)
   - `policy_gate.py`: lazy-load mit env-var `POLICY_GATE_CONFIG_PATH` für Test-Injection
   - 45 Tests: pytest fixture für tmp policy_gate.json
5. **`hooks/session_check.py` Migration**:
   - `hooks/session_check.json` (top-level keys: `staleness_days_threshold: 90`, `check_paths`, `policy_version: "1.0"`)
   - `references/schemas/session-check.schema.json`
   - Hard-Sync-Comment in `session_check.py:22` updaten auf neuen `validate_schema.py`-Pfad (bleibt scripts/, kein Wechsel zu bin/)
   - 34 Tests
6. **`scripts/audit_preflight.py` + `scripts/check_convergence.py` + `scripts/escalation_decision.py`** (gemeinsamer Commit, kleine Skripte):
   - `references/audit-triggers.yaml` (8 Trigger + 2 Count-Based)
   - `references/convergence-rules.yaml` (NUR Konstanten: `DETERMINISTIC_SUBSET`, `GRADE_LETTERS`, `DEFAULT_MAX_VARIANCE`)
   - `references/escalation-rules.yaml` (NUR Konstanten: `GRADE_BOUNDARIES`, `ESC1_PROXIMITY`, `ESC3_DIVERGENCE`)
   - 3 thin readers (~50 LOC each), CLI-Contracts frozen
   - Predikate (`if abs(score-boundary)≤proximity`, `deterministic_match AND grade_variance_ok AND null_ok`) bleiben Code (Right-Altitude L82-84: set ops + bool logic)

### Stufe 3 — `validate_schema.py` + `validate_token_budgets.py` (2 Commits)

7. **`validate_schema.py` thin reader** + 6 JSON-Schemas:
   - `references/schemas/{ref-file,skill,agent,research,domain-cache,hooks-json}.schema.json`
   - `validate_schema.py` (~80 LOC): behält custom `StrictStringsLoader` (yaml-Coercion-Fix nötig); behält `parse_frontmatter()`; ruft `jsonschema.validate()`
   - Module-level Funktionen `validate_date`, `parse_frontmatter`, `validate_*_files` bleiben importable für Tests
8. **`validate_token_budgets.py` thin reader**:
   - `skills/review-claude-config/references/token-budgets.json` (43 BUDGETS + DOMAIN_CACHE_BUDGET als glob-Eintrag + DEFAULT_BUDGET)
   - `validate_token_budgets.py` (~50 LOC): JSON-load + per-file-loop + WARN/PASS/FAIL-classification mit gleichen Diagnostics wie heute
   - Module-level `BUDGETS` re-exported via lazy-load für Test-Backward-Compat

### Stufe 4 — Verifikation + Doku-Sweep (2 Commits)

9. **Snapshot-Tests + byte-identical-verification**:
   - `tests/fixtures/refactor-snapshot/{merge,convergence,escalation,audit}-pre-refactor.json`
   - `tests/test_refactor_byte_identical.py` (subprocess-Aufruf, diff stdout+stderr+exit-code für 4 thin reader)
10. **Doku-Sweep**: `grep -rn` über CLAUDE.md, README.md, CONTRIBUTING.md, docs/*.md, agents/*.md, skills/**/SKILL.md, .github/workflows/*.yml + Update auf neue Pfade. ~20+ Stellen.

## Kritische Files

**Modifiziert:**
- `scripts/{merge_findings,validate_schema,validate_token_budgets,check_convergence,escalation_decision,audit_preflight}.py` (Konstanten raus, lazy-load via PEP 562)
- `hooks/{policy_gate,session_check}.py` (Konstanten raus, lazy-load + env-var-Injection)
- `hooks/hooks.json` (Konvention: `policy_gate.json` + `session_check.json` Pfade)
- `Makefile` (3 Target-Updates + shellcheck-Integration in lint)
- `.github/workflows/{ci,release-please}.yml` + neuer `policy-consistency.yml`
- `skills/review-claude-config/references/scoring-rubric.md` (Stufe 0: 3 neue normative Tabellen-Sektionen)
- `skills/review-claude-config/references/agent-evaluation-guide.md` (Header-Notiz auf scoring-rubric.md §Agent Items)
- `tests/test_*.py` (11 Files; minimal-invasiv via lazy-load + module-level proxy)
- `CLAUDE.md` (§Architecture: bin/-Konvention, scripts/issue-state.sh-Disposition)
- `CONTRIBUTING.md` (shellcheck-Prerequisite)
- `skills/review-skill/SKILL.md` (auditieren auf Pfad-Drift, ggf. nachgezogen — keine Frozen-Contract-Drift erwartet)
- ~20 Doku-Stellen

**Gelöscht:**
- `scripts/sync-marketplace-ref.py` (NUR dieses; validate_schema/validate_token_budgets bleiben Python)

**Neu:**
- `bin/sync-marketplace-ref.sh` + `bin/.gitkeep`
- `scripts/regenerate_merge_policy.py` (Parser-Skript, SOT-C+)
- `skills/review-skill/references/merge-policy.yaml` (AUTO-GENERATED-Header)
- `skills/review-claude-config/references/audit-triggers.yaml`
- `skills/review-claude-config/references/convergence-rules.yaml` (Konstanten)
- `skills/review-claude-config/references/escalation-rules.yaml` (Konstanten)
- `skills/review-claude-config/references/token-budgets.json`
- `skills/review-claude-config/references/schemas/{ref-file,skill,agent,research,domain-cache,hooks-json,policy-gate,session-check}.schema.json` (8 Stück)
- `skills/review-claude-config/references/schemas/CONVENTIONS.md`
- `hooks/policy_gate.json`, `hooks/session_check.json`
- `.github/workflows/policy-consistency.yml`
- `tests/fixtures/refactor-snapshot/*.json`
- `tests/test_refactor_byte_identical.py`
- `tests/test_bin_smoke.py`
- `tests/test_regenerate_merge_policy.py`
- `Plans/audit-rubric-eval-rightaltitude.md` (Stufe-0.1-Output)

## Verifikation

Pro Commit (`make validate` exit 0):
- `ruff check hooks/ scripts/`
- `ruff format --check hooks/ scripts/`
- `python3 scripts/validate_schema.py`
- `python3 scripts/validate_token_budgets.py`
- `pytest tests/ -v`
- `shellcheck bin/*.sh` (ab Stufe 0.3, hard-required)

Vor PR-Open zwingend:
- `make validate` mehrfach grün auf jedem Stufen-Endpunkt
- `/review-skill skills/review-skill/SKILL.md`
- `/review-hook hooks/hooks.json`
- `/check-repo-health all`
- `/audit-context-budget .` (delta vs `main`)
- `/validate-primitive-dependencies .`
- `git diff origin/main..HEAD | grep -E '/Users/'` (zwingend leer)
- `git log --show-signature` (alle Commits signiert)
- Pre-PR-Spike-Ergebnisse aus Stufe 0.1 dokumentiert + User-Approvals festgehalten
- `tests/test_refactor_byte_identical.py` grün
- PR-Description-Checkbox "Pre-flight session closed in commit `<SHA>`"

## Backward-Compatibility (verbindlich)

1. **Test-Imports + Lazy-Load-Cache-Semantik**: lazy-load via PEP 562 `__getattr__` erhält alle Module-Level-Konstanten als importierbare Symbols. **Cache-Semantik präzisiert**: `__getattr__` cached **nicht** in `__dict__` — bei jedem Read wird `_load_policy()` aufgerufen, das selbst `@functools.lru_cache(maxsize=1)` auf der yaml-Load-Funktion hat (Process-Level-Cache). Damit ist `monkeypatch.setattr(module, "CONSTANT_NAME", ...)` deterministisch reversibel: setattr schreibt in `__dict__`, Read findet es dort vor `__getattr__`-Fallback; `monkeypatch.undo()` löscht via `delattr` aus `__dict__`, nachfolgende Reads gehen wieder durch `__getattr__` → frische lru_cache-Lookup. Test-Isolation garantiert. Tests müssen NICHT umgeschrieben werden für Cat-B-Skripte. Mocking-Pattern in `references/schemas/CONVENTIONS.md` dokumentiert.
2. **CLI-Args**: Frozen-Contract-Tabelle verbindlich; alle 4 thin reader exit-codes/stderr identisch.
3. **`validate_schema.py` + `validate_token_budgets.py`**: bleiben aufrufbar als `python3 scripts/...py`.
4. **`sync-marketplace-ref.py`**: gelöscht, ersetzt durch `bin/sync-marketplace-ref.sh`. Konsumenten-Repos die sie direkt aufrufen brechen → Major-Version-Bump v3.0.0 via `BREAKING CHANGE:`-Footer in Stufe-1-Commit.
5. **Re-export-Removal-Roadmap**: Re-exports werden NICHT in diesem PR entfernt. Plan v3.x trägt sie weiter; eine spätere Major-Bump-PR (≥v4.0.0) räumt sie auf, wenn alle Konsumenten migriert haben. Roadmap-Eintrag in `CHANGELOG.md` mit "Tracked-for-removal: module-level re-exports of YAML-loaded constants in merge_findings/policy_gate/session_check etc."

## Risiken & Mitigation

1. **CLI-Drift** → Frozen-Contract-Tabelle + Snapshot-Test (Stufe 4)
2. **Test-Imports brechen** → lazy-load via PEP 562 `__getattr__`; `RuntimeError` bei fehlender YAML statt `ImportError` (verbindlich)
3. **Mid-Session-Freeze rubric-Edit** → Stufe 0 in separater Session, abgeschlossen via `chore(session): close pre-flight` Marker-Commit; PR-Description-Checkbox als Audit-Trail
4. **rubric.md-Format zu lose für Parser** → Stufe 0.2 erweitert rubric.md um 3 normative pipe-delimited Tabellen (~120 LOC neu); Parser bleibt trivial (~80 LOC)
5. **`policy_gate.json` und `session_check.json` getrennt** → reduziert blast radius (gelernte Lektion aus Reviewer F1)
6. **Reviewer-Findings übersehen** → Runde 2 abgeschlossen; Runde 3 nach diesem Update als Konvergenz-Smoke-Test
7. **Plugin-Konsumenten ohne shellcheck/jq** → CONTRIBUTING.md dokumentiert Prerequisites; `make lint` hard-required (kein graceful-degrade — Reviewer B2 gefolgt)
8. **`scripts/issue-state.sh`** bleibt unverschoben → CLAUDE.md §Architecture-Eintrag dokumentiert Konvention "scripts/ für ≥100-LOC-Skripte mit Pipeline-State; bin/ für ≤30-LOC-Bash-Helper"
9. **Stufe-0.1-Audit-Findings** (rubric_binary_evaluator, perspective_certificate_parser) → User-Approval-Gate per AskUserQuestion: in PR aufnehmen oder follow-up Issue (Default: follow-up Issue für Scope-Control)
10. **`policy-consistency.yml` CI-only ohne pre-commit** → bewusste Wahl (User-Decision #3 war "ODER"); CI-fail genügt als drift-detection. **Workflow-Konvention dokumentiert** in CONTRIBUTING.md: jede `scoring-rubric.md`-Edit MUSS im selben Commit `merge-policy.yaml` regenerieren (`python3 scripts/regenerate_merge_policy.py`); CI fail-only (kein bot-auto-commit) erzwingt das.

11. **Schema-Versioning forward-compat** → `policy_version: "1.0"` ist heute nur Annotation. Thin-reader-Verhalten **lenient**: bei `version` außerhalb `["1.0"]` wird Warning auf stderr ausgegeben + best-effort-Read (kein Abbruch). Major-Bump zu `"2.0"` erfordert dann separaten Migration-PR mit explizitem `_load_policy_v2()`-Pfad. Roadmap-Eintrag in CHANGELOG.

## Quellen

- [arXiv 2603.13287 — From Stochastic Answers to Verifiable Reasoning](https://arxiv.org/abs/2603.13287)
- [Anthropic Engineering — Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

## Implementation Status (post-Approval, 2026-05-04)

**Stufe 0 (Pre-flight) abgeschlossen.** Plan-Abweichung von "1 atomarer PR mit Squash-Merge" zu **"Multi-Commit direkt auf main"** — entstanden durch parallel-User-Arbeit während der Stufe-0.1-Audits liefen, dokumentiert hier damit nachfolgende Stufen den effektiven Modus kennen.

**Geschehen:**

| Commit | Inhalt | Pfad |
|---|---|---|
| `b8c20fe` (PR #181) | Stufe 0.3 (bin/-Konvention: Makefile, CLAUDE.md, CONTRIBUTING.md) + Stufe 1 Commit 1 (`bin/sync-marketplace-ref.sh` + `scripts/sync_marketplace_ref.py` deletion + `release-please.yml` update) als gebündelter User-Commit | direkt auf main via PR |
| `1aa76f0` | `tests/test_bin_smoke.py` | mit-gemerged in #181 |
| `c6a053f` | Plan + Audit-Reports + Spike-Report | direkt auf main |
| `fd036fe` | Stufe 0.2 (rubric mit 3 normativen Tabellen + Token-Budget 10300→12000) + agent-evaluation-guide.md cross-ref | direkt auf main |
| `b392e38` | Stufe-0-Close-Marker (`chore(session): close pre-flight session`) | direkt auf main |

Plus: Issue #184 für markdown-it-py-Spike als `track: post-ga` gefilet (Spike-Output: ROI negativ, defer).

**Effektiver Workflow (User-bestätigt 2026-05-04):**
- Direkt auf `main` ohne Feature-Branch-PR (Solo-Maintainer-Pattern)
- Pro Stufe-Commit: `make validate` grün vor Push
- Conventional Commits + SSH-Signatur
- `BREAKING CHANGE:`-Footer NUR wenn echte Konsumenten-API bricht (z. B. Stufe 1 sync-marketplace-ref)

**Konsequenz für Stufe 2+:**
Der ursprünglich geplante "atomare PR" entfällt. Stattdessen wird **jeder Plan-Commit (#2 bis #10) einzeln auf `main` gepusht**, jeder grün auf `make validate`. Wenn der Maintainer für eine spezifische Stufe doch einen PR-Review-Pfad bevorzugt (z. B. Stufe 2 Commit #3 `merge_findings.py` mit lazy-load via PEP 562 — substantielle Behavior-Änderung trotz gefrorener CLI), kann er pro Stufe entscheiden und feature-Branch + PR wählen.

**Stufe 0.1 Audit-Verdicts (verbindlich):**
- `rubric_binary_evaluator.py` (1726 LOC): **0/0/0 Verstöße** — alle 28 Check-Funktionen deterministisch. Repo-eigener Anti-Varianz-Beleg hält stand. Keine PR-Erweiterung.
- `perspective_certificate_parser.py` (333 LOC): markdown-it-py-Migration **bedingt machbar (110-160 LOC, ROI negativ)** → Issue #184, `track: post-ga`. Keine PR-Erweiterung.

**Plan-Inventar-Korrektur (echte Code-Daten aus `scripts/merge_findings.py`):**
- `BINARY_ITEM_IDS`: 32 ✓
- `NARRATIVE_PARENT_IDS`: **15** (Plan-Inventar listete 14)
- `ITEM_DIMENSION`: **33** (Plan: 32)
- `BINARY_CAPS`: **22** (Plan: 20)
- `AGENT_ITEM_DIMENSION`: **35** (Plan: 26)

`scoring-rubric.md` reflektiert die echten Zahlen. Stufe 2 Commit #2 (`regenerate_merge_policy.py` Parser) muss gegen diese Counts emittieren.

**Stufe 2+ Eintrittspunkt:**
Nächste Session beginnt mit Plan-Commit #2 (`scripts/regenerate_merge_policy.py` + initial `merge-policy.yaml` + `policy-consistency.yml`). Frische Session zwingend: scoring-rubric.md ist mid-session-frozen, der Parser MUSS die erweiterten Tabellen mit frischem KV-Cache lesen.

## Stufe 2 Progress (2026-05-04, second session)

| Commit | SHA | Inhalt | Verifikation |
|---|---|---|---|
| #2 | `e119169` | `scripts/regenerate_merge_policy.py` (244 LOC) + `skills/review-skill/references/merge-policy.yaml` (146 LOC, AUTO-GENERATED) + `.github/workflows/policy-consistency.yml` (24 LOC, fail-only drift gate) + `tests/test_regenerate_merge_policy.py` (7 tests) | `make validate` exit 0; reviewer SHIP after 3 polish-edits applied (F3/F6/F10) |
| #3 | `3a5e168` | `scripts/merge_findings.py` lazy-load via PEP 562 `__getattr__` + `tests/test_merge_findings.py` (3 new TestLazyLoadPolicy tests) + `ruff.toml` (per-file F821 ignore). Net diff: −106 LOC. | `make validate` exit 0 (985 tests); reviewer FIX-FIRST → T1 (full-message regex) + T2 (monkeypatch-reversibility test) applied; rebased onto release-bot v2.4.0 commit, sig preserved |

**Migration scope cut (user-confirmed analysis 2026-05-04):**
- 5 Konstanten migriert (rubric-derived): `BINARY_ITEM_IDS`, `NARRATIVE_PARENT_IDS`, `ITEM_DIMENSION`, `BINARY_CAPS`, `AGENT_ITEM_DIMENSION`
- 4 Konstanten bleiben Code (Right-Altitude L82-84 — narrowly algorithmic, single-consumer math): `OVERLAP_THRESHOLD`, `GRADE_TO_NUMERIC`, `GRADE_ORDER`, `SEVERITY_RANK`
- 1 Konstante deferred zu Issue #187: `dimension_owners` (function-local, besserer SoT-Pfad ist agent-frontmatter-derivation, nicht yaml)

**Reviewer-Befunde verschoben auf post-Stufe-2:**
- A1: `scripts/_lazy_yaml.py` Extraktion — Rule of Three, warten bis Commit #4 (`policy_gate.py`) + #5 (`session_check.py`) den Pattern wiederholen
- A2: `references/policy-paths.yaml` Konstanten-Registry — bundle in A1 follow-up
- S1/S2/D1: Polish (Function-Indirection, dead defensive AttributeError, längerer error-message hint) — non-blocking
