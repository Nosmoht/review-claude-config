# Spike: perspective_certificate_parser.py → markdown-it-py

**Datum**: 2026-05-04  
**Auditor**: Explore-Subagent (Stufe 0.1b)  
**Quelle**: scripts/perspective_certificate_parser.py (333 LOC), tests/test_perspective_certificate_parser.py

## Was wird heute geparst (kurz)

Der Parser konsumiert ein Markdown-Zertifikat mit strikter Struktur:
- **Preamble**: Optionale Prosa am Anfang (wird toleriert trotz "no preamble"-Rule)
- **Frontmatter-Splittin**: Drei kanonische Sektion (`### Perspective`, `### Certificate`, `### Findings`)
- **Certificate-Block**: Markdown-Tabelle mit 8 Zeilen (7 benannte Dimensionen + "Overall", der gedropt wird)
- **Findings-Extraktion**: State-Machine iteriert über `#### Finding (...)` Header, parst Klammer-Metadaten (severity, dimension, checklist_item, primary_focus, owner_conflict, hint_owner), dann extrahiert 5 kanonische Felder (Evidence, Why it matters, Validation, Current, Recommended) aus Multiline-Bodies
- **Lenient-Pfade**:
  - Preamble vor `### Perspective` wird gedropt (nicht fehlgeschlagen)
  - Fehlende Separator (`---`) nach Findings ist ok
  - Off-spec Grades (z.B. "Critical" statt A-F) werden stillschweigend gedropt
  - Haiku indentiert Labels manchmal unter nested list items; Parser toleriert bis zu 4 Leerzeichen
  - Felder mit `<= 4 Spaces` Indentation sind noch Label-Erkennungen; `>= 5 Spaces` sind Code-Block-Inhalt (wörtlich erhalten)
  - ERROR-Shortcut: `### ERROR\n<reason>` wird als `{'error': reason}` emittiert, alles andere wird ignoriert
  - Fehlende Felder im Finding-Header (z.B. `hint_owner: null` fehlt) führen nicht zu Fehler, nur zu leeren Defaults

## Test-Korpus

**Umfang**: 47 Testfälle in `tests/test_perspective_certificate_parser.py`

**Kategorien**:

1. **Captured Fixtures (2 Testfälle)**: Zwei echte Haiku-Captures aus Pilotphase
   - `clear_antecedent_01`: 9 Findings (High/Medium/Low), vollständig
   - `clear_antecedent_02`: 6 Findings, validiert gegen JSON-Schema

2. **Strukturelle Edge-Cases (5 Testfälle)**:
   - Minimal cert (no findings) ✓
   - Prosa-Preamble toleriert ✓
   - "Overall" wird aus dimensions gedropt ✓
   - Off-spec Grade ("Critical") wird gedropt ✓
   - ERROR Shortcut (`### ERROR\n<reason>`) ✓
   - Empty markdown (keine Sektion) ✓
   - perspective_override parameter ✓

3. **Header-Metadaten-Parsing (4 Testfälle)**:
   - Severity-Normalisierung (High/HIGH/high → "High", etc.) ✓
   - Boolean-Parsing (true/True/yes/false/False/no) ✓
   - hint_owner Parsing (null/None/string-value) ✓
   - ID-Kanonisierung (`<item>:<path>:<dim>/v1`) ✓

4. **Body-Field-Parsing (7 Testfälle)**:
   - Multiline Evidence ✓
   - Multiline Current/Recommended (mit leeren Zeilen) ✓
   - Separator (`---`) wird nicht ins Body-Feld geleckt ✓
   - Zwei Findings werden korrekt separiert ✓
   - Perspective wird in alle Findings getragen ✓
   - **Indented Label Recovery**: Labels mit 0-4 Spaces Indentation werden erkannt; ≥5 Spaces sind Code-Block-Inhalt ✓
   - Deeply-indented Label als Codeblock-Content (Test mit 5+ Spaces) ✓

5. **Pipeline-Interop (1 Testfall)**:
   - Parser-Output lädt sauber in `merge_findings.merge_directory()` ✓

## markdown-it-py-Verfügbarkeit

**Status**: NICHT installiert in diesem Repo

**pyproject.toml-Check**: 
- `dependencies = ["pyyaml>=6.0", "jsonschema>=4.20"]`
- `markdown-it-py` ist NICHT gelistet
- Müsste als neue Dependency hinzugefügt werden (transitive Abhängigkeit: `markdown-it-py` selbst hat `mdurl`, `uc.micro` als Deps — minor)

**Installation**: `pip install markdown-it-py` ~0.5 MB, stabil seit 2.0.0 (2023), aktiv maintained

## Machbarkeit-Bewertung

### Verdict: **bedingt machbar in 80-150 LOC** — mit signifikanten Lenient-Trade-offs

### Begründung:

`markdown-it-py` ist ein **vollständiger CommonMark-Parser mit Plugin-Architektur**, nicht ein Lenient-Markdown-Splitter. Die Kernlogik des Parsers folgt jedoch **nicht** der `markdown-it`-Standard-Philosophie, sondern ist **domänenspezifisch**:

1. **Was `markdown-it-py` NATIV unterstützt**:
   - Tabellen-Parsing (via `table` plugin, wird standardmäßig aktiviert in `markdown-it-py`)
   - Heading-Extraktion (`### Perspective`, etc.)
   - Fenced-Code-Block vs. regular-text Unterscheidung (Indentation)
   → Diese könnten Token-Tree-Traversal ersetzen

2. **Was NICHT ersetzt wird — domänenspezifische Lenient-Logik**:
   - **Comma-split des Finding-Headers** (`#### Finding (severity: ..., dimension: ..., ...)`) — Das ist keine Markdown-Struktur, sondern **Haiku-generiertes Pseudo-CSV in Parens**. `markdown-it` tokenisiert das als `text`, nicht als strukturiertes Format. Müsste mit eigenem Regex gelöst bleiben.
   - **5-Zeilen-Field-Label-Extraktion** (`Evidence:`, `Why it matters:`, etc.) — Das ist **domänenspezifisches Key:Value-Extraktion aus Plain Text**, nicht Markdown. `markdown-it` gibt Inline-Token zurück, aber `"Why it matters: foo\nbar"` als einen `text`-Token — manuelles Parsing des Inhalts bleibt nötig.
   - **Lenient Indentation-Toleranz** (≤4 spaces = Label, ≥5 spaces = code) — `markdown-it` hat eigene Regeln für Code-Indentation (4 spaces = code block, nicht 5). Würde zu Inkompatibilität führen.
   - **Preamble-Dropping vor `### Perspective`** — Müsste noch manuell via Token-Filterung erfolgen.
   - **Multi-Finding-Split** — `markdown-it` würde alle `#### Finding ...` als separate Headings exposieren, aber das Linking zur Body-Content bleibt manuell.

3. **Realistisches Refactor-Szenario**:
   ```
   ≈50-70 LOC: markdown-it tokenization + heading/table extraction
   ≈40-60 LOC: Custom Finding-header & field-body parsing (praktisch identisch zum Original)
   ≈20-30 LOC: Integration + error handling
   ────────────────────────────────
   ≈110-160 LOC (nicht ≤80)
   ```

4. **Lenient-Loss-Analyse**:
   - **Indentation-Schwelle**: `markdown-it` standardisiert auf 4-space-code-block, nicht 5. Der Parser toleriert Labels bis 4 Spaces; `markdown-it` behandelt 4 spaces bereits als code-block-Start. **Test `test_indented_label_recovered_within_threshold` würde FAIL**, weil `  Why it matters:` (2 spaces) wäre immer noch text, aber die `    Validation:` (4 spaces) könnte als inline-code interpretiert werden je nach context.
   - **Custom lenient parsing** von Haiku-Drift bleibt essentiell — `markdown-it` macht das nicht besser, es macht es kompliziert.

5. **Verifizierung der 47 Tests**:
   - ✓ Captured Fixtures: Wahrscheinlich grün (table + heading extraction works)
   - ✓ Structural EdgeCases: Grün (preamble, overall-drop, error-shortcut sind alle oberhalb Markdown)
   - ⚠️ Indentation threshold tests: **Risiko auf FAIL** — `markdown-it`'s code-block rules sind strenger
   - ✓ Header-metadata parsing: Grün (regex split bleibt unverändert)
   - ⚠️ Body-parsing: **Grün theoretisch, aber Code-Indentation-Semantik ändert sich**
   - ✓ Pipeline-interop: Grün (JSON structure unverändert)

## Empfehlung

- [ ] **In Refactor-PR aufnehmen (Item #10)** — nicht empfohlen. ROI negativ.
- [x] **Als follow-up Issue filen (Default für Scope-Control)**
- [ ] "Bewusst akzeptiert" — kein Migrationspfad lohnt

**Begründung der Empfehlung**:  
Der Parser ist **nicht die klassische AST-Traversal** unter Right-Altitude-Regel L44. Er ist **domänenspezifische Haiku-Output-Dekodierung**, bei der die "Lenient-Regeln" (Indentation-Schwelle, Label-Toleranz, Preamble-Dropping) geschäftskritisch sind. Eine `markdown-it-py`-Migration würde:

1. Die komplexeste Logik (Finding-header-parsing, field-body-extraction) nicht reduzieren
2. Zusätzliche Komplexität durch `markdown-it`-Tokenization-Overhead einführen
3. Indentation-Edge-Cases neu kalibrieren müssen → Test-Brüche
4. Abhängigkeit auf `markdown-it-py` (transitive Deps) hinzufügen ohne Code-Reduktion

**Besser**: Das Skript als `Haiku-Decoder` (Spezialfall) behandeln, nicht als "Parser mit etablierter Lib". Falls später eine zweite Perspektive oder ein anderes Format hinzukommt: erst dann Abstraktion evaluieren.

---

**Status**: Spike geschlossen. Keine Aktion erforderlich. Ergebnis in Plans/ dokumentiert.
