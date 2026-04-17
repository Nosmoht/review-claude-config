# Plan: Phase 1 — Plane-Projekt-Anlage für FlugFunkApp (Session B)

**Revision:** v2 (nach 3-Perspektiven-Review; 10 High + 11 Medium + 6 Low Findings adressiert)

## Context

Master-Plan `wondrous-wishing-bee.md` §"Phase 1" legt die einmalige Anlage des Plane-Projekts "FlugFunk" fest, damit post-Phase-1.5 jede weitere Arbeit über Plane-Tasks orchestriert wird. ADR-006 (`Proposed`, committed) fixiert das Hybrid-Ownership-Modell (Plane = Tasks/Findings/Sprint; Repo = ADRs/Research/Specs/Code) und benennt Plane's **Built-in Issue-Feld `external_id`** als Idempotenz-Key mit Invariante `external_id = <repo-artifact-id>-<sha8>`. Die Sync-Mechanik (Hook vs. Skill) ist auf ADR-007 verschoben, zu autoren in exakt dieser Session *basierend auf* der hier gemessenen Token-Kosten (Decision darf erst nach Messung fallen). Die erste Plane-Write triggert den Hard-Gate "new external service" aus `.claude/rules/hard-gates.md` — Ledger-Entry + `unblock: approved` sind prozessual verpflichtend. Guardrail 9: CWD außerhalb `FlugFunkApp/`; Commits per `git -C $HOME/workspace/FlugFunkApp ...` (nicht `cd ... && git`, um CWD-Drift zu vermeiden).

## Scope & Deliverables

1. Session-Start-Token-Baseline (vor allen Writes).
2. Hard-Gate-Ledger-Entry im `hard-gates.md`-konformen Format; User-Unblock.
3. Early `chore(adr): reserve ADR-007 slot` Commit (ADR-Number-Race-Prevention).
4. Plane-Projekt "FlugFunk" (Identifier `FFU`) mit Workflow-States, Labels, Custom-Properties, Views-Spec-Page + parallelem Repo-File.
5. Entitäten-Inventur-Gate + Smoke-Test mit Property-Persistenz-Check.
6. Token-Cost-Report (Delta zwischen Baseline und Post-Setup).
7. Hook-Research-Snapshot nach FlugFunkApp.
8. ADR-007-Draft (Option-Matrix + Decision basierend auf Stage-7-Zahlen).
9. Multi-Perspective-Review via FlugFunkApp-eigene Review-Agents (peer-reviewer, traceability-auditor, architecture-decider).
10. Atomic Commit-Sequenz.

## Stage 0 — Session-Start-Baseline (READ-ONLY, capture)

**Zweck:** Token-Cost-Baseline **vor** jeglichem Plane-Tool-Call messen, damit Stage 7 echtes Delta ausweist.

- Capture der Tool-Schema-Registry-Size via `ToolSearch`-Meta (tool_count + durchschnittliche Schema-Bytes, falls via API introspectable) und `/context`-Output.
- Speichern in Session-Scratch-File `$HOME/workspace/FlugFunkApp/docs/runtime/plane-bootstrap-state.local.json` (gitignored, neu anlegen):
  ```json
  {"baseline": {"ts": "2026-04-17T...", "context_tokens_pre": <n>, "tool_registry_bytes": <n>}}
  ```
- `.gitignore` prüfen: falls `docs/runtime/*.local.json` nicht ignoriert, Zusatz-Entry (eigenes kleines Commit-Pair, Commit-Message `chore: ignore local runtime state files`).

## Stage 1 — Hard-Gate Ledger-Update (EDIT `session-ledger.md`)

**Scope:** NUR den existierenden "Phase 1 Hard-Gate Entry (2026-04-17)"-Block (Zeilen 5–13 im aktuellen Ledger) ersetzen. `## Current state`, `## Highest-priority next tasks`, `## Hard-gate watchlist`, `## Resume rule` bleiben unberührt (A2 F11).

**Neuer Block-Inhalt** (exakt nach `hard-gates.md` Bullet-Struktur; H2-Heading als Ergänzung, nicht Regel-Abweichung):
```markdown
## Phase 1 Hard-Gate Entry (2026-04-17)
- gate reason: add new external service (Plane integration — first project-creation write)
- affected task: Phase-1 Plane-Projekt-Anlage (Plans/jaunty-stirring-cherny.md)
- proposed options: proceed with Plane project write | defer to manual UI-only setup | abandon Plane integration
- exact unblock needed: unblock: approved
```

User trägt `unblock: approved` unter den Block. Session pausiert bis zu diesem Trigger.

## Stage 2 — ADR-007 Placeholder-Commit (Early, race-prevention)

**Rationale:** `adr-draft-from-research` §Preconditions fordert reservierten ADR-Slot vor Full-Draft-Invocation. Placeholder sofort nach Unblock platzieren, damit keine parallel-Session denselben Slot greift.

**File:** `$HOME/workspace/FlugFunkApp/docs/decisions/ADR-007-placeholder.md` (Filename-Präzedenz aus `ADR-006-placeholder.md`; `ADR-*.md`-Glob in `scripts/traceability_check.py` matcht theoretisch, aber:
- FlugFunkApp hat **keine** aktiven pre-commit-Hooks (`.git/hooks/*.sample` only, keine `.pre-commit-config.yaml`; `claude_hook.py` läuft async PostToolUse ohne Block) — verifiziert in Review.
- `traceability_check.py` läuft nur bei manuellem `review_gate.py`-Call. Placeholder-Lebensdauer beträgt Minuten (Stage 2 → Stage 9b).
- Plan-explizite Instruktion: Zwischen Stage 2 und Stage 9b **kein** `python3 scripts/traceability_check.py`-Aufruf.

**Content** (3 Zeilen, Pattern-Match zu ADR-006-Placeholder `8c86b34`):
```markdown
# ADR-007 Placeholder

Reserved slot for the plane-sync mechanic ADR.

Full content lands in a follow-up commit that replaces this file with `ADR-007-plane-sync-mechanic.md`.
```

Commit 1: `chore(adr): reserve ADR-007 slot for plane-sync mechanic`
Via: `git -C $HOME/workspace/FlugFunkApp add docs/decisions/ADR-007-placeholder.md && git -C $HOME/workspace/FlugFunkApp commit -m "..."`

(Commit 0 — Ledger-Update — wird **nach** Stage 2 als Commit 2 gebucht, damit Ledger bereits den Unblock enthält und der Placeholder atomar die erste Write-Operation ist. Begründung: Ledger ohne Unblock ist inkonsistent, Ledger mit Unblock ist aber auch ein aktiver State-Change → besser bündeln.)

**Aktualisierung Commit-Reihenfolge:** Ledger-Edit und Placeholder in einem Commit → `docs(ledger): unblock phase-1 hard-gate and reserve ADR-007 slot` (kombiniert, weil beide Schreibe-Operationen vom selben Unblock abhängen). Scope `docs(ledger)` ist neu, aber inhaltlich korrekt (A2: `runtime` nie als Scope genutzt; `ledger` ist passender).

## Stage 3 — Preflight (READ-ONLY Plane-Calls)

1. `mcp__plane__get_me` → User-UUID + Workspace-Membership-Role prüfen (muss `admin` oder `member` sein für `create_project`).
2. `mcp__plane__list_projects` mit `fields="id,name,identifier,external_id,external_source"` → verifizieren, dass kein Projekt mit `external_id="project-flugfunk"` existiert (Re-run-Sicherheit).
3. **Search-Filter-Capability-Probe** (Review A1 F6): Falls `list_projects` Filter `external_id` im Response-Body unterstützt, `search_work_items`-Idempotenz-Pfad ist sicher. Falls nur full-list: Plan fällt auf Client-seitigen Scan zurück — Info im State-File notieren.
4. `mcp__plane__list_states` / `mcp__plane__list_labels` → nur falls Plane-Default-States existieren, Namen + UUIDs erfassen (Konflikt-Matrix).

Update `plane-bootstrap-state.local.json`:
```json
{"preflight": {"user_uuid": "...", "workspace_role": "...", "existing_default_states": [...], "filter_capability": "..."}}
```

## Stage 4 — Projekt anlegen (WRITE)

`mcp__plane__create_project`:
- `name="FlugFunk"`, `identifier="FFU"`
- `is_issue_type_enabled=true`, `cycle_view=true`, `page_view=true`, `issue_views_view=true`, `module_view=false`, `intake_view=false`
- `project_lead=<user-uuid>` (Kommentar: wirkt nur als Ownership-Markierung, nicht als Access-Restriction für andere Workspace-Members)
- `external_source="flugfunkapp-repo"`, `external_id="project-flugfunk"`

Response `id` → State-File:
```json
{"project_id": "...", "created_at": "..."}
```

## Stage 5 — Strukturen (States, Labels, Work-Item-Type)

**Idempotenz-Protokoll pro Entität:** `list_*` → existiert mit matching `external_id`? → skip + UUID reusen. Sonst `create_*`. Response → State-File. 

**State-Default-Konflikt-Strategie** (A1 F5): Falls Plane Default-States angelegt hat, je Ziel-State-Namen: wenn Name identisch → `update_state` (rename oder only-color-set); wenn neuer Name → Default beibehalten + neuen anlegen (Plan fordert **nicht** Delete von Defaults, da Side-Effects unbekannt). Exception: wenn mehr als 1 State `default:true` hat, unseren "Backlog" als `default:true` setzen, existierenden Default auf `false` via `update_state`.

### States (6)
| name | group | color | default |
|---|---|---|---|
| Backlog | backlog | #94A3B8 | true |
| Ready | unstarted | #3B82F6 | false |
| In Progress | started | #F59E0B | false |
| In Review | started | #A855F7 | false |
| Done | completed | #10B981 | false |
| Blocked | cancelled | #EF4444 | false |

Jeder `external_id="state-<slug>"`.

### Labels (25)
Kategorien × Werte mit `external_id="label-<cat>-<val>"`:
- `priority`: P0 (#DC2626), P1 (#F97316), P2 (#FACC15), P3 (#16A34A)
- `status`: in-progress (#3B82F6), in-review (#A855F7), blocked (#EF4444), done (#10B981)
- `category`: corpus, research, adr, task, review, verify, infra, primitive-update, product
- `phase`: iphone, android-blocked
- `type`: finding, task, decision, consolidation, migration, refactor

### Work-Item-Type
`mcp__plane__list_work_item_types` → prüfen (Plane legt Default bei `is_issue_type_enabled=true` an). Reusen falls vorhanden, sonst `create_work_item_type("Task", is_epic=false, external_id="type-task")`. Response `id` → State-File (`type_id`).

## Stage 6 — Custom Properties (4, blockt durch type_id)

`mcp__plane__create_work_item_property` × 4 (sequentiell nach type_id):

| display_name | property_type | options/settings |
|---|---|---|
| `phase` | OPTION | options=[{name:"iphone"},{name:"android-blocked"}], is_multi=false |
| `blocked_by` | RELATION | relation_type="ISSUE", is_multi=true |
| `repo_artifact_path` | TEXT | settings={display_format:"single-line"} |
| `repo_external_id` | TEXT | settings={display_format:"single-line"} |

**Naming-Klärung:** Plane-Built-in `external_id` (Issue-Attribut) bleibt **der eigentliche Idempotenz-Key** gemäß ADR-006-Invariante. Die Custom-Property `repo_external_id` ist nur eine **redundante, user-facing Anzeige** für Board-Filterbarkeit. Diese Klarstellung gehört in ADR-007 Consequences (nicht in ADR-006-Amendment) — ADR-006 bleibt korrekt, weil die Invariante das Built-in-Feld meint.

Jede Property `external_source="flugfunkapp-repo"`, `external_id="prop-<name>"`. Response → State-File.

## Stage 7 — Views-Spec (Dual: Repo + Plane-Page)

**Authoritativ:** Write `$HOME/workspace/FlugFunkApp/docs/project/plane-views-spec-2026-04-17.md` mit 5 View-Definitionen:
- Current Phase Board (Filter: `phase=iphone`, Group: state)
- Findings Queue (Filter: `label=type:finding`, Sort: priority desc)
- Consolidation Pipeline (Filter: `label=category:corpus`)
- All Tasks by Category (Group: label category)
- Dependencies Graph (via `blocked_by` Property)

Jede View als Section: `Purpose / Filter / Group / Sort`.

**Render-Copy:** `mcp__plane__create_project_page` mit `name="Views Specification (Phase 1)"`, `description_html` = HTML-gerenderte Version des Repo-Files, `external_id="page-views-spec"`. Plane-Page ist KEIN Source (ADR-006); Repo-File ist.

## Stage 8 — Entitäten-Inventur-Gate (READ-ONLY)

Fail-fast-Check vor Smoke-Test:
- `list_states` → count == 6
- `list_labels` → count == 25
- `list_work_item_types` → count >= 1 (mit "Task")
- `list_work_item_properties` → count == 4 (phase, blocked_by, repo_artifact_path, repo_external_id)
- `list_projects` → "FlugFunk" mit `external_id=project-flugfunk` sichtbar

Bei Abweichung: Plan abbrechen, State-File-Diff melden, User-Intervention.

## Stage 9 — Smoke-Test

Item wird erstmal im Live-Projekt angelegt (Prefix `smoke-` + Delete macht es rückgängig; kein separates Test-Projekt da Cleanup durch Delete verifiziert wird).

1. `mcp__plane__create_work_item`:
   - `name="SMOKE-TEST 2026-04-17: delete me"`
   - `state=<Backlog-UUID aus State-File>`
   - `priority="low"`
   - `labels=[<label-category-task>, <label-type-task>]`
   - Custom-Property `phase="iphone"` (A3 F7: Property-Persistenz testen)
   - `external_source="flugfunkapp-repo"`, `external_id="smoke-2026-04-17"`
   → `ISSUE_ID`.
2. `mcp__plane__retrieve_work_item` mit `expand="state,labels,properties"`. Assertions:
   - `external_id == "smoke-2026-04-17"`
   - `state` = Backlog-UUID
   - `labels` enthält beide Label-UUIDs
   - Property `phase == "iphone"` (kritisch)
3. `mcp__plane__search_work_items` mit Filter `external_id="smoke-2026-04-17"` → exakt 1 Match. Falls Filter unsupported (Preflight Stage 3.3 negativ): `list_work_items` + Client-Filter.
4. `mcp__plane__delete_work_item`.
5. `mcp__plane__retrieve_work_item` → 404.

## Stage 10 — Token-Cost-Report

Delta-Messung (A1 F7, A3 F2):
- Baseline aus Stage 0 State-File (pre-writes)
- Aktuelle Werte (post-Smoke-Test): `/context` + Tool-Registry-Size
- `delta_tokens = post - pre`

File: `$HOME/workspace/FlugFunkApp/docs/project/plane-mcp-token-cost-2026-04-17.md`

Struktur:
- **Methodologie**: Tool Search deferred, Baseline vs. Post-Setup, Mess-Limits
- **Messung**: `tool_count`, `schemas_auto_loaded`, `context_pre`, `context_post`, `delta`, approximated Tokens (`bytes/4`), `% of 200K budget`
- **Vergleich vs. ADR-006-Threshold**: 5 % (`delta / 200000 * 100`)
- **Programm-Budget-Projektion**: `delta × 19` für 17–21 Folge-Sessions
- **Empfehlung**: Scoped-Activation ja/nein + Implikation für ADR-007-Option

## Stage 11 — Hook-Research-Snapshot

Source-Policy: Nur repo-lokale Sources in ADR-007. Kopiere:
- Quelle: `$HOME/workspace/review-claude-config/research/hook-observation/hook-based-runtime-observation-patterns.md`
- Ziel: `$HOME/workspace/FlugFunkApp/docs/research/hook-based-runtime-observation-patterns.md`

Provenance-Header am Anfang der Ziel-Datei anfügen:
```markdown
---
original: review-claude-config/research/hook-observation/hook-based-runtime-observation-patterns.md
snapshot_date: 2026-04-17
snapshot_reason: source-policy compliance for ADR-007 citation
---
```

## Stage 12 — Pre-ADR-007 Sources-Verification

Shell-Check vor Skill-Invocation (A3 F12):
```bash
for p in \
  docs/project/primitive-inventory-2026-04-17.md \
  docs/research/plane-mcp-spike-2026-04-17.md \
  docs/project/plane-mcp-token-cost-2026-04-17.md \
  docs/research/hook-based-runtime-observation-patterns.md \
  docs/decisions/ADR-006-plane-integration.md \
  .claude/rules/hard-gates.md \
  CLAUDE.md ; do
  test -f "$HOME/workspace/FlugFunkApp/$p" || echo "MISSING: $p"
done
```

Alle grün → Stage 13. Sonst fix fehlende Files.

## Stage 13 — ADR-007 Draft im Staging

Draft-Ort: Working-Tree-File `$HOME/workspace/FlugFunkApp/docs/decisions/ADR-007-plane-sync-mechanic.md` (uncommitted) — Review-Agents lesen via absoluten Pfad. Iterations-Log in temporärem Markdown-Block im `plane-bootstrap-state.local.json` unter `adr007_review_iterations`.

**Decision-Logik (nicht vor-determiniert; A3 F4):**
- **Pre-Requisite:** Stage 10 Token-Cost-Zahl + Hook-Research-Evidence vorliegen.
- **Options-Matrix** (im Draft unter Context):
  - A: Hybrid — PostToolUse-Hook + `plane-sync`-Skill für Reconcile
  - B: Skill-only (explizite Invocation pro Session)
  - C: Hook-only (ohne Reconcile)
- **Entscheidung** basierend auf Token-Cost + Hook-Research:
  - Wenn `delta > 5%` Single-Session-Budget → Option A mit scoped Hook-Activation, oder Option B (Skill weniger invasiv bei hohem Budget).
  - Wenn `delta ≤ 5%` → Option A Primary (Hybrid ist ergonomisch besser).
  - Option C bleibt in allen Fällen rejected (kein Reconcile-Pfad für manuelle Repo-Edits).

**Nygard-Struktur strict:**
- **Status:** `Proposed`
- **Context** (2 Absätze, mit inline `<kind>:<path>`-Refs zu `adr:docs/decisions/ADR-006-plane-integration.md`, `research:docs/research/plane-mcp-spike-2026-04-17.md`, `research:docs/research/hook-based-runtime-observation-patterns.md`)
- **Decision:** 1 positiver Bullet für gewählte Option (Rejection-Rationales der anderen Optionen gehen in Consequences-Sub-Bullet "Alternatives considered")
- **Consequences:** Primitive-Impact-Liste + Alternatives-considered-Sub-Block + Open: ADR-008 (retry/idempotency)
- **Sources** (ADR-006-Pattern, Tier-separiert):
  - *Tier-1 extern:* docs.claude.com MCP-Config-Referenz, Plane-Server-README (bereits in `plane-mcp-spike` snapshotted)
  - *Repo-Kontext-Refs:*
    - `docs/project/primitive-inventory-2026-04-17.md`
    - `docs/research/plane-mcp-spike-2026-04-17.md`
    - `docs/project/plane-mcp-token-cost-2026-04-17.md`
    - `docs/research/hook-based-runtime-observation-patterns.md`
    - `docs/decisions/ADR-006-plane-integration.md`
    - `.claude/rules/hard-gates.md`
    - `CLAUDE.md`

## Stage 14 — Multi-Perspective-Review (uncommitted Draft)

Dispatch (parallel) von FlugFunkApp-Review-Agents:
- `peer-reviewer` (Convention-Compliance, Nygard-Struktur, Sources-Tier-Separation)
- `traceability-auditor` (`<kind>:<path>`-Ref-Check, Sources `test -f`-Validity, Enum-Konformität)
- `architecture-decider` (Decision-Rationale + Option-Matrix auf Stimmigkeit mit Token-Zahl)

Falls Review-Agents nicht existieren: Fallback auf `peer-reviewer`-Plan-Agent-Prompt (review-claude-config). Finding-Gate: Zero Medium vor Commit.

Iterationen in State-File loggen.

## Stage 15 — Commit-Sequenz (atomic, finale Ordering)

`git -C $HOME/workspace/FlugFunkApp ...` für alle Commits (kein `cd`):

1. **Commit 1** (nach Stage 1 + Stage 2): `docs(ledger): unblock phase-1 hard-gate and reserve ADR-007 slot`
   - Diff: Ledger-Hard-Gate-Block ersetzt + `docs/decisions/ADR-007-placeholder.md` neu
2. *(Stages 3–9: Plane-API-Writes, keine Repo-Commits)*
3. **Commit 2** (nach Stage 10): `docs(project): add plane mcp token cost report`
   - Diff: `docs/project/plane-mcp-token-cost-2026-04-17.md` neu
4. **Commit 3** (nach Stage 11): `docs(research): snapshot hook-based runtime observation patterns`
   - Diff: `docs/research/hook-based-runtime-observation-patterns.md` neu (+ Provenance-Header)
5. **Commit 4** (nach Stage 14 grün): `docs(adr): add ADR-007 plane-sync mechanic (proposed)`
   - Diff: `docs/decisions/ADR-007-placeholder.md` DELETED + `docs/decisions/ADR-007-plane-sync-mechanic.md` NEW (atomare Substitution im selben Commit)
6. **Commit 5** (Session-End): `docs(ledger): record phase-1 completion`
   - Diff: Ledger bekommt einen Status-Block "Phase 1 complete 2026-04-17, see commits <sha1>..<sha5>"

Optional vor Commit 1: `chore: ignore local runtime state files` falls Gitignore erweitert werden muss (Stage 0).

## Critical Files

**Read-only:**
- `$HOME/workspace/review-claude-config/Plans/wondrous-wishing-bee.md` (Master-Plan)
- `$HOME/workspace/FlugFunkApp/.claude/rules/hard-gates.md`
- `$HOME/workspace/FlugFunkApp/.claude/rules/source-policy.md`
- `$HOME/workspace/FlugFunkApp/.claude/rules/traceability.md`
- `$HOME/workspace/FlugFunkApp/.claude/skills/adr-draft-from-research/SKILL.md`
- `$HOME/workspace/FlugFunkApp/.claude/skills/adr-draft-from-research/references/adr-template.md`
- `$HOME/workspace/FlugFunkApp/docs/decisions/ADR-006-plane-integration.md`
- `$HOME/workspace/FlugFunkApp/docs/project/primitive-inventory-2026-04-17.md`
- `$HOME/workspace/FlugFunkApp/docs/research/plane-mcp-spike-2026-04-17.md`
- `$HOME/workspace/review-claude-config/research/hook-observation/hook-based-runtime-observation-patterns.md`
- `$HOME/workspace/FlugFunkApp/scripts/traceability_check.py` (nur zur Glob-Verifikation)
- `$HOME/workspace/FlugFunkApp/.gitignore`

**Write/Create (über Plan-Verlauf):**
- `$HOME/workspace/FlugFunkApp/docs/runtime/session-ledger.md` (Hard-Gate-Block ersetzen)
- `$HOME/workspace/FlugFunkApp/docs/runtime/plane-bootstrap-state.local.json` (Resume-Cache, gitignored)
- `$HOME/workspace/FlugFunkApp/docs/decisions/ADR-007-placeholder.md` (transient, in Commit 4 gelöscht)
- `$HOME/workspace/FlugFunkApp/docs/project/plane-views-spec-2026-04-17.md` (Repo-authoritativ)
- `$HOME/workspace/FlugFunkApp/docs/project/plane-mcp-token-cost-2026-04-17.md`
- `$HOME/workspace/FlugFunkApp/docs/research/hook-based-runtime-observation-patterns.md` (Snapshot mit Provenance)
- `$HOME/workspace/FlugFunkApp/docs/decisions/ADR-007-plane-sync-mechanic.md` (final)

## Reused Utilities

- Skill `adr-draft-from-research` — für Draft-Validierung (test -f Sources).
- Agents `peer-reviewer`, `traceability-auditor`, `architecture-decider` (FlugFunkApp `.claude/agents/`) — für Stage 14 Multi-Review.
- `scripts/traceability_check.py` — Post-Commit-Validator (nach Commit 4).
- Plane-MCP-Tools (deferred-loaded).

## Verification (Exit-Code-Deterministisch)

1. `claude mcp list` → `plane: ✓ Connected`.
2. `mcp__plane__list_projects` zeigt `identifier=FFU` + `external_id=project-flugfunk`.
3. `mcp__plane__list_states` count = 6 (Stage 8 automated).
4. `mcp__plane__list_labels` count = 25 (Stage 8 automated).
5. `mcp__plane__list_work_item_properties` count = 4 (Stage 8 automated).
6. Smoke-Test (Stage 9) alle 5 Sub-Schritte grün inkl. Property-Persistenz.
7. `test -f` auf alle 7 ADR-007-Sources grün (Stage 12).
8. `git -C $HOME/workspace/FlugFunkApp log --oneline -5` zeigt genau 5 Commits (Commit 1 = Ledger+Placeholder, 2 = Token-Cost, 3 = Snapshot, 4 = ADR-007-Final, 5 = Ledger-Completion).
9. `python3 $HOME/workspace/FlugFunkApp/scripts/traceability_check.py` → Exit 0.
10. Stage 14 Review-Agents: Zero Medium-Findings (State-File logged).
11. `cat $HOME/workspace/FlugFunkApp/docs/project/plane-mcp-token-cost-2026-04-17.md` enthält konkrete Delta-Zahl + 5%-Threshold-Vergleich + ADR-007-Entscheidungs-Input.
12. `cat $HOME/workspace/FlugFunkApp/docs/runtime/session-ledger.md` hat Unblock + Phase-1-Completion-Block; Resume-Rule-Section und andere unberührt.

**Rollback-Pfade:**
- **Vor Commit 1:** Plain abort; Ledger-Edit via git checkout rückgängig.
- **Zwischen Commit 1 und Commit 4:** `git revert <sha>` pro Commit. Plane-Seitig: `delete_project(PROJECT_ID)` **nur mit User-Freigabe**. Default: State-File behalten, Re-run wird via `external_id`-Pre-Check idempotent.
- **Nach Commit 4:** ADR-007 bleibt; Plane-Setup bleibt; Session darf enden.

**Abbruch-Mitte-Stage-5-Szenario:** State-File (gitignored) enthält alle bisher erzeugten UUIDs. Re-run-Session-Start prüft State-File zuerst, überspringt erledigte Stages, setzt ab Stage X fort.

## Out of Scope (diese Session)

- Keine Plane-Tasks anlegen (Phase 1.5, Session C).
- Keine Primitive-Updates aus der 11er-Liste (Folge-Sessions).
- Keine `plane-sync`-Implementierung (nach ADR-007-Accept).
- Keine Chats-Konsolidierung.
- Keine Änderungen an review-claude-config-Skills.
- Kein ADR-006-Amendment (Naming-Klärung geht in ADR-007 Consequences, ADR-006-Invariante bleibt unverändert).

## Review-Trail (diese Plan-Version)

Diese Revision adressiert 23 Findings aus 3-Agent-Kritik:
- **HIGH fixes:** Commit-Ordering (Placeholder früh), Token-Baseline-Pre-Stage-0, Decision nicht pre-determiniert, State-File-Cache, Scope `docs(ledger)`, Ledger-Section-Schutz, Idempotenz-Key-Klarstellung, Sources-Tier-Split, Review-Agents statt Plan-Agents, Placeholder-Glob-Risiko dokumentiert.
- **MEDIUM fixes:** `git -C` statt `cd`, Smoke-Test mit Property-Persistenz, Stage-8-Inventur-Gate, Plane-UI-Checks ersetzt durch `list_*`-Counts, State-Default-Konflikt-Strategie, Search-Filter-Preflight-Probe, Views-Spec-Repo-Backup, Draft-Staging-Location explizit, Commit-Count in Verification korrigiert, Test-Namespacing via `smoke-`-Prefix.
- **LOW fixes:** `project_lead`-Dokumentation, Placeholder-git-history als `delete+add` bewusst akzeptiert, Traceability-inline-refs im ADR-007-Context.

## Lessons from Session B (post-hoc, 2026-04-17)

Session B lieferte 8 Commits statt der im Plan spezifizierten 5. Nach einer 3-Perspektiven-Post-Hoc-Review (Architektur-Sonderheit, Prozess-Drift, Design-Erosion) sind folgende Punkte ins Template für Phase 1.5 und Folge-Sessions aufzunehmen:

- **Read-before-Edit bei Templated-Creates.** Die Snapshot-Datei Stage 11 wurde via `cp` + `Edit` erzeugt. Der `Edit`-Call schlug fehl, weil die Datei noch nicht gelesen war (Harness-Regel); der Provenance-Header landete erst in einem Fix-up-Commit (`9ccddc0`). Für zukünftige Sessions: nach jedem `cp` oder `Write` von templated Dateien immer `Read` vor `Edit`, um Fix-up-Commits zu vermeiden. Alternative: direkt via `Write` mit dem finalen Inhalt inklusive Provenance-Header, statt `cp` + `Edit`.
- **Commit-Count-Toleranz in Verification.** Die Plan-v2-Zeile „`git log --oneline -5` zeigt genau 5 Commits" ist zu rigide. Optional-Commits (z.B. `chore: ignore local runtime json state files` zur Gitignore-Erweiterung) und Fix-up-Commits bei nicht-vermeidbaren Harness-Fehlern erhöhen die Zahl. Ein Plan-v3 sollte lauten: „≥ 5 benannte Phase-1-Commits in korrekter Scope-Reihenfolge; zusätzliche `chore:`/Fix-up-Commits sind zulässig, wenn im Session-Ledger-Completion-Block dokumentiert".
- **Views-Spec-Commit-Zuordnung explizit.** Stage 7 produziert ein Views-Spec-Repo-File, aber Stage 15 Commit-Sequenz nennt es nicht. Die Commit-Tabelle muss Stage 7 als eigenen Commit oder als Teil von Commit 2 (Token-Cost) ausweisen; implizite Bündelung ist kein kontrolliertes Verhalten.
- **Plane-Instance-Capability-Probe vor Plan-Finalisierung.** Plan v2 nahm das volle Plane-Feature-Set (Work-Item-Types, Properties, Views-API, Project-Pages) als gegeben an. Die installierte Community-Edition liefert HTTP 404 auf alle diese Endpoints. Zukünftige Plan-Sessions sollten in Phase 0 oder Stage 3 (Preflight) einen Capability-Probe-Schritt haben, der jeden geplanten Schreibpfad mit einem minimalen Read-Call testet, bevor Stages 4–6 designed werden. Vermeidet Mid-Execution-Plan-Abweichungen.
- **Fix-up-Commit-Squash nicht möglich ohne `-i`-Flag.** Globales CLAUDE.md verbietet `git rebase -i`. Ein post-hoc-Squash von Fix-up-Commits ist damit nur über destruktive Non-interaktive-Rewrites (reset --mixed + Re-Commit) möglich, die SHAs invalidieren und upstream committed Referenzen (z.B. im Session-Ledger) nachziehen. Im Trade-off wiegt der irreführende `git blame` weniger als der Rewrite-Risiko. Lesson: Fix-up-Commits akzeptieren, Hygiene durch Read-before-Edit-Disziplin präventiv sichern.
- **Mid-Execution-Plan-Deviation-Protokoll.** Beim HTTP-404-Ereignis in Stage 5/6 wurde der Plan ad-hoc angepasst und die Begründung nur im State-File dokumentiert. Plan-v3 sollte ein explizites Deviation-Template definieren: Abweichung, Rationale, betroffene Stages, Downstream-Implikation, ADR-Referenz. Im aktuellen Flow landete die ADR-Referenz erst im ADR-007 §Consequences, das ist vertretbar aber nicht systematisch.
