# Prompt-/Context-First Tightening

## Summary

Erster Schritt ist ein sauberer Revert des begonnenen Python-Ausbaus: entferne den untracked `scripts/`-Baum, `hooks/policy_gate.py`, `hooks/post_write_validate.py` und ersetze diesen Plan durch die schlankere Variante. Es werden keine neuen Python-Dateien eingeführt und keine neue Runtime- oder Eval-Engine gebaut.

Die Umsetzung bleibt prompt-/context-first: bessere Review-Prompts, schärfere Rubrik, konsistentere Reports, path-first Analytics, korrigierte Maintainer-Workflows und aktualisierte Doku. Die bestehenden Hooks `skill_quality_gate.py` und `session_check.py` bleiben die einzige Python-Basis.

## Umsetzung

### 1. Review-Vertrag und gemeinsame Guidance

- Halte die bestehenden Review-Kommandos und die bestehende Report-Grundform.
- Schärfe die Review-Prompts so, dass jede Empfehlung evidenzbasiert ist: Heading mit `Impact` und `Category`, danach `Evidence:`, kurze Begründung, `Current:`/`Recommended:` falls anwendbar und `Validation:` für den Re-Check.
- Ziehe `scoring-rubric.md`, `engineering-baseline.md` und die drei typspezifischen Evaluation Guides gemeinsam auf dieselbe Linie: Trigger-Präzision, Coexistence/Isolation, Third-Person-Beschreibungen, explizite Verifikation, flache Referenzstruktur und keine zeitabhängige Sprache.
- Füge keine neuen Tools zu den Review-Skills hinzu.

### 2. Reports, Analytics und Apply-Kompatibilität

- Kein Schema-v2-, Fingerprint- oder Adapter-Projekt.
- `review-analytics` verwendet `type + path` als primäre Identität und `name` nur noch als Display-Label.
- Wenn derselbe Pfad über mehrere Reports hinweg existiert, bleibt es dieselbe Linie, auch bei geändertem Namen.
- Wenn ein Pfad verschwindet und ein neuer auftaucht, meldet Analytics einen Rename/Move-Kandidaten statt still per Name zu mergen.
- `apply-review-findings` und die typspezifischen Apply-Skills bleiben kompatibel, weil `Current:`/`Recommended:` und die Summary-Struktur erhalten bleiben.

### 3. Hook-, Maintainer- und Doku-Layer

- Reverte die neuen Hook-Skripte vollständig.
- Nutze weiter nur die bestehenden Hooks; keine neue Enforcement-Logik.
- Straffe `hooks/guidelines.md` zu einer kürzeren, signalstärkeren Checkliste, die zu Rubrik und Baseline passt.
- Korrigiere `check-repo-health`, damit die reale Repo-Struktur geprüft wird und nicht mehr `## File Structure` vorausgesetzt wird.
- Ändere `scaffold-skill` und sein Template auf `[plugin|maintenance] <skill-name>`.
- Plugin-Modus registriert neue Skills nur in vorhandenen Zielbereichen von `README.md` und `CLAUDE.md`; Maintenance-Modus ändert nur `CLAUDE.md`.
- Generator und Template dürfen nicht mehr auf `## Skills`, `## File Structure` oder `## Installation` als Registrierungspunkte verweisen.
- Ergänze manuelle Review-Regressionsfälle als Markdown-Dokumentation statt einen automatisierten Runner einzuführen.
- Aktualisiere `README.md` und `CLAUDE.md` so klar dokumentiert ist: prompt/context first, bestehende Hooks bleiben, Grades sind Zusammenfassungen und kein Beweis.

## Öffentliche Änderungen

- `/scaffold-skill` wird zu `[plugin|maintenance] <skill-name>`.
- Review-Findings bekommen verpflichtend `Evidence:` und `Validation:` bei weiterhin bestehendem `Current:`/`Recommended:`-Muster.
- `review-analytics` wertet Verläufe path-first statt name-first aus.
- Es gibt keinen neuen CLI- oder Python-Runner.

## Test Plan

- Nach dem Revert gibt es keine der neu eingeführten Python-Dateien mehr.
- Ein Self-Review des Repos erzeugt Findings mit `Evidence:` und `Validation:` in allen Review-Typen.
- `apply-review-findings` und die typspezifischen Apply-Skills bleiben mit den neuen Reports lesbar.
- `review-analytics` behandelt denselben Pfad als dieselbe Linie und meldet Pfadwechsel als Kandidaten.
- `check-repo-health` läuft gegen die aktuelle Repo-Struktur ohne falsches `## File Structure`.
- `scaffold-skill` trennt Plugin- und Maintenance-Modus korrekt in Prompt, Template und Registrierungszielen.
- `python3 -m py_compile hooks/session_check.py hooks/skill_quality_gate.py` bleibt erfolgreich.

## Annahmen

- Es werden keine neuen Python-Dateien eingeführt.
- Die bestehenden Python-Hooks bleiben Teil des Systems, weil sie bereits Baseline-Verhalten des Repos sind.
- Manuelle Markdown-Regressionen reichen für diesen Patch aus; ein automatisierter Eval-Runner ist ausdrücklich nicht Teil dieses Plans.
- Rename-/Move-Erkennung bleibt konservativ: Analytics meldet Kandidaten statt automatisch zu mergen.
