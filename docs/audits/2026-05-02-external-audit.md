# Wissenschaftliches Audit: `Nosmoht/review-claude-config`

**Rolle:** externe professorale Begutachtung für AI-/LLM-Agentensysteme  
**Datum:** 2026-05-02  
**Repository:** <https://github.com/Nosmoht/review-claude-config>  
**Ziel:** inhaltliche Optimierung von Skills, Agents, Hooks, Rules/References, Research-/Evidence-Layer und Review-/Apply-Flows.  
**Status dieser Fassung:** review-fähige, quellenkritisch gehärtete Übergabefassung. Sie ist vollständig als konzeptionelles und methodisches Repo-Audit, aber nicht als empirischer Wirksamkeitsnachweis. Nicht belastbare Sekundärquellen wie Wikipedia, Reddit, Hacker News, News-Artikel, allgemeine Blogs und vendor-ferne Zusammenfassungen werden nicht als Evidenz für normative Claims verwendet.

---

## 1. Executive Summary

Das Repository ist konzeptionell stark: Es behandelt Claude-Code-Artefakte nicht als lose Prompt-Sammlung, sondern als **auditierbares Qualitätssystem für agentische Workflows**. Die Grundarchitektur ist plausibel und durch Produkt-Primärquellen sowie aktuelle Agentenforschung gestützt:

- **Skills** kapseln prozedurales Wissen und Workflows.
- **Agents/Subagents** trennen Review-Perspektiven und Kontexte.
- **Hooks** bilden eine deterministische Kontroll- und Observability-Schicht.
- **Rules/References/Rubrics** stabilisieren Bewertungskriterien.
- **Skripte** übernehmen deterministische Checks, um LLM-Varianz zu reduzieren.
- **Evidence-Layer** versucht, wissenschaftliche und produktbezogene Claims explizit zu klassifizieren.

**Gesamturteil:** B+ mit realistischem A-Potenzial.  
**Hauptgrund:** Der Inhalt ist sehr gut ausgerichtet, aber noch nicht ausreichend empirisch validiert. Die größte Lücke ist nicht fehlende Theorie, sondern fehlende Messung: Golden Dataset, Ablation Studies, Inter-Run-Stabilität, False-Positive-/False-Negative-Raten und Kosten-/Nutzen-Metriken.

**Wichtigste Korrektur gegenüber einer rein positiven Bewertung:** Das Repo darf nicht den Eindruck erzeugen, alle Rubric-Items und Workflow-Entscheidungen seien gleichermaßen wissenschaftlich bewiesen. Mehrere starke Komponenten sind **Engineering Guidance** oder **Repo Default**, nicht `Proven result`.

---

## 2. Prüfauftrag und Methodik

### 2.1 Forschungsfrage

> Sind die im Repository enthaltenen Skills, Agents, Hooks, Rules/References und Research Results inhaltlich korrekt, wissenschaftlich plausibel, vollständig genug und optimierbar, um Claude-Code-Konfigurationen zuverlässig zu auditieren und zu verbessern?

### 2.2 Bewertungslogik

Dieses Audit trennt vier Ebenen:

| Ebene | Bedeutung | Zulässige Schlussfolgerung |
|---|---|---|
| **Produkt-Primärquelle** | Offizielle Anthropic-/Claude-Code-Dokumentation | Aussagen über intendierte Claude-Code-Funktionalität |
| **Wissenschaftliche Primärquelle** | peer-reviewed Paper oder arXiv-Preprint mit klarer Kennzeichnung | Aussagen über empirische Befunde oder Benchmarks |
| **Security-/Engineering-Standard** | OWASP, RFCs, Spezifikationen, etablierte Standards | Risiko- und Kontrollanforderungen |
| **Repo-interne Evidenz** | README, Skills, Agents, Hooks, Research Notes, Rubrics | Untersuchungsgegenstand; nicht automatisch externe Evidenz |

### 2.3 Verwendete Evidenzklassen

Die Einordnung folgt dem repo-internen Evidence-Maintenance-Modell:

- **Proven result**: direkt durch starke Primär-/Benchmark-Evidenz gestützt.
- **Engineering guidance**: durch Produktdokumentation, Standards oder solide technische Forschung gestützt, aber nicht als universeller wissenschaftlicher Satz bewiesen.
- **Repo default**: lokale Konvention, Schwelle oder Workflow-Entscheidung.
- **Low-evidence area**: plausibler, aber wissenschaftlich schwach belegter Bereich.

### 2.4 Nicht verwendete Quellen

Nicht beweisführend verwendet:

- Wikipedia
- Reddit/Hacker News
- News-Artikel
- unkuratierte Blogposts
- Marketing-Zusammenfassungen
- Medium-/LinkedIn-Posts ohne Primärstatus
- AI-generierte Sekundärzusammenfassungen

Diese Quellen können für private Orientierung nützlich sein, sind aber für ein wissenschaftlich reviewbares Übergabedokument nicht ausreichend.

### 2.5 Vollständigkeitsstatus dieser Fassung

Diese Fassung ist **vollständig für eine qualifizierte Übergabe an den Repository-Autor**, weil sie:

- den Untersuchungsgegenstand abgrenzt,
- die Evidenzklassen definiert,
- schwache Quellen als Beweisgrundlage ausschließt,
- zentrale Produkt-, Security- und Forschungsquellen trennt,
- die Architektur nach Skills, Agents, Hooks, Rules/References, Research/Evidence und Apply-Flows bewertet,
- konkrete Change Requests formuliert,
- eine Coverage-Gap-Matrix enthält,
- zentrale Audit-Claims claim-by-claim klassifiziert,
- offene Unsicherheiten nicht als bewiesene Tatsachen darstellt.

Diese Fassung ist **nicht vollständig als empirischer Nachweis der Wirksamkeit des Repositories**. Dafür fehlen Ergebnisse, die nur durch den Repository-Autor oder Maintainer erhoben werden können:

- Golden-Dataset-Messungen,
- Precision/Recall pro Finding-Klasse,
- Inter-Run-Stabilität,
- Ablation Studies,
- External-Validity-Tests auf Fremdrepos,
- Kosten-/Latenzmetriken,
- Hook-False-Block-/Missed-Policy-Raten.

Daraus folgt: Das Dokument darf als **wissenschaftlich kontrolliertes Audit und Verbesserungsplan** verwendet werden, aber nicht als Behauptung, dass das System bereits empirisch validiert ist.

---

## 3. Validierte Kernquellen

### 3.1 Produkt-Primärquellen

1. **Anthropic: Effective context engineering for AI agents**  
   Quelle: <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>  
   Relevanz: Kontext ist endliche Aufmerksamkeit; gute Kontextarchitektur sucht die kleinste hochsignalige Tokenmenge.  
   Evidenzklasse: Engineering guidance.

2. **Anthropic: Equipping agents for the real world with Agent Skills**  
   Quelle: <https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills>  
   Relevanz: Skills als paketierte prozedurale Expertise; Progressive Disclosure als Kernprinzip.  
   Evidenzklasse: Engineering guidance.

3. **Claude Code Docs: Hooks Guide**  
   Quelle: <https://code.claude.com/docs/en/hooks-guide>  
   Relevanz: Hooks bieten deterministische Kontrolle über Claude-Code-Verhalten.  
   Evidenzklasse: Engineering guidance für Claude-Code-spezifische Runtime-Kontrolle.

4. **Claude Code Docs: Hooks Reference**  
   Quelle: <https://code.claude.com/docs/en/hooks>  
   Relevanz: Hook-Events, Input/Output-Formate, Konfiguration, asynchrone Hooks.  
   Evidenzklasse: Product-primary.

5. **Claude Code Docs: Subagents**  
   Quelle: <https://code.claude.com/docs/en/sub-agents>  
   Relevanz: Subagents laufen in separatem Kontextfenster mit eigenem System Prompt, Tool Access und Permissions.  
   Evidenzklasse: Product-primary.

6. **Claude Code Docs: Best Practices**  
   Quelle: <https://code.claude.com/docs/en/best-practices>  
   Relevanz: Hooks für Aktionen, die jedes Mal ohne Ausnahme passieren müssen; CLAUDE.md eher advisory.  
   Evidenzklasse: Product-primary.

### 3.2 Wissenschaftliche / Benchmark-Quellen

1. **AGENTIF: Benchmarking Instruction Following of LLMs in Agentic Scenarios**  
   Quelle: <https://arxiv.org/abs/2505.16944>  
   Relevanz: Agentische Instruktionen sind lang und constraint-reich; aktuelle Modelle haben Probleme mit Tool- und Constraint-Strukturen.  
   Evidenzklasse: Preprint evidence / Proven result für den Benchmark-Befund, nicht für alle Repo-Schlussfolgerungen.

2. **AgentDojo: Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents**  
   Quelle: <https://arxiv.org/abs/2406.13352>  
   Relevanz: Tool-using agents sind anfällig für Prompt Injection durch untrusted data; Evaluation realistischer Tool-Agenten nötig.  
   Evidenzklasse: Preprint evidence / Security-relevant benchmark evidence.

3. **Survey on LLM-as-a-Judge**  
   Quelle: <https://arxiv.org/html/2411.15594>  
   Relevanz: LLM-Judges brauchen Reliability-Strategien, Bias-Kontrolle und geeignete Evaluationsmethoden.  
   Evidenzklasse: Survey evidence.

4. **Can You Trust LLM Judgments? Reliability of LLM-as-a-Judge**  
   Quelle: <https://arxiv.org/html/2412.12509>  
   Relevanz: Inter-rater agreement allein reicht nicht, um LLM-Judge-Reliability vollständig zu erfassen.  
   Evidenzklasse: Preprint evidence.

### 3.3 Security-Standards

1. **OWASP Top 10 for LLM Applications**  
   Quelle: <https://owasp.org/www-project-top-10-for-large-language-model-applications/>  
   Relevanz: LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, LLM05 Supply Chain, LLM06 Excessive Agency, LLM10 Unbounded Consumption.  
   Evidenzklasse: Security-standard.

2. **OWASP AI Agent Security Cheat Sheet**  
   Quelle: <https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html>  
   Relevanz: Agentenspezifische Risiken, Kontrollmodelle und Governance.  
   Evidenzklasse: Security-standard.

### 3.4 Repo-interne Primärartefakte

- README: <https://github.com/Nosmoht/review-claude-config>
- Docs: <https://github.com/Nosmoht/review-claude-config/tree/main/docs>
- Research: <https://github.com/Nosmoht/review-claude-config/tree/main/research>
- Skills: <https://github.com/Nosmoht/review-claude-config/tree/main/skills>
- Agents: <https://github.com/Nosmoht/review-claude-config/tree/main/agents>
- Hooks: <https://github.com/Nosmoht/review-claude-config/blob/main/hooks/hooks.json>
- Scientific Research Dossier: <https://raw.githubusercontent.com/Nosmoht/review-claude-config/refs/heads/main/docs/scientific-research-dossier.md>
- Evidence Maintenance Guide: <https://raw.githubusercontent.com/Nosmoht/review-claude-config/refs/heads/main/docs/evidence-maintenance.md>
- Dimension Evidence Coverage Matrix: <https://raw.githubusercontent.com/Nosmoht/review-claude-config/refs/heads/main/docs/dimension-evidence-coverage.md>

---

## 4. Problemstellung

Das Repository ist ein Meta-System: Es bewertet und verändert Claude-Code-Primitives, also genau jene Artefakte, die später Agentenverhalten steuern. Daraus folgen sechs Kernprobleme.

### 4.1 Constraint Overload

Agentische Instruktionen enthalten Rollen, Toolgrenzen, Outputverträge, Ausnahmebedingungen und Sicherheitsregeln. AGENTIF zeigt, dass solche langen und komplexen Constraint-Settings für LLMs ein reales Problem sind.

**Implikation für das Repo:** Lange Skills, große Rubrics und komplexe Review-Flows erhöhen nicht nur Review-Qualität, sondern auch Fehlerrisiko. Kontextdisziplin ist deshalb kein Stilthema, sondern ein Zuverlässigkeitsthema.

**Evidenzklasse:** Proven result für die allgemeine Schwierigkeit; supported inference für dieses Repo.

### 4.2 LLM-Judge-Reliability

Das Repo nutzt LLMs als Reviewer. LLM-as-a-Judge ist nützlich, aber muss kalibriert werden: Bias, Inkonstanz, Severity Drift und Over-Agreement sind bekannte Risiken.

**Implikation:** Multi-Agent-Review und deterministische Binary Checks sind sinnvoll, aber nicht ausreichend. Es braucht Messung: Inter-Run-Stabilität, goldene Referenzfälle und Fehleranalyse.

**Evidenzklasse:** Survey evidence / supported inference.

### 4.3 Prompt Injection und Tool-Risiko

Claude-Code-Artefakte können externe Inhalte, WebFetch, Bash, Write/Edit, Hooks und Subagents einbeziehen. Dadurch entstehen klassische Agentenrisiken: Prompt Injection, Excessive Agency, Sensitive Data Leakage und unsichere Tool-Nutzung.

**Implikation:** Hooks, least privilege, Write-Gates und explizite Apply-Grenzen sind inhaltlich richtig. Das Repo sollte diese Logik aber stärker als Security-Modell dokumentieren.

**Evidenzklasse:** Security-standard / Engineering guidance.

### 4.4 Progressive Disclosure vs. Runtime-Bloat

Agent Skills sollen Wissen gestuft laden. Wenn `SKILL.md` selbst zu lang wird, wird Progressive Disclosure unterlaufen.

**Implikation:** Das Repo sollte seine eigenen Skills gegen ein Token-/Instruction-Bloat-Budget prüfen, nicht nur Ziel-Repos.

**Evidenzklasse:** Product-primary / supported inference.

### 4.5 Evidenz vs. Heuristik

Das Repo erkennt im eigenen Evidence-Maintenance-Guide bereits an, dass nicht alle Claims gleich stark sind. Diese Trennung ist korrekt, aber muss noch konsequenter in Rubric, Findings, Reports und Apply-Flows erscheinen.

**Implikation:** Jedes Finding sollte ausweisen: `evidence_class`, `inference_type`, `source_refs`, `uncertainty`, `auto_apply_allowed`.

**Evidenzklasse:** Repo default plus Engineering guidance.

### 4.6 Meta-Review-Security

Ein zu prüfender Skill kann selbst instruktionelle Angriffe gegen den Reviewer enthalten. Das ist eine spezielle Variante von indirect prompt injection: Der Reviewer liest ein Artefakt, das Anweisungen enthält, die nicht befolgt werden dürfen.

**Implikation:** Das Repo braucht einen expliziten Threat Model Abschnitt: „reviewed artifacts are untrusted input“.

**Evidenzklasse:** supported inference aus OWASP/AgentDojo.

---

## 5. These, Antithese, Synthese

### 5.1 These

Das Repository verfolgt den richtigen Grundansatz:

> Semantische Bewertung durch LLMs, deterministische Verifikation durch Skripte und Hooks, Perspektiventrennung durch Subagents, Reproduzierbarkeit durch Rubrics und Evidence-Layer.

Diese These wird gestützt durch:

- Anthropic Context Engineering: kleine, hochsignalige Kontexte.
- Anthropic Agent Skills: Progressive Disclosure.
- Claude Code Hooks: deterministische Kontrollpunkte.
- Claude Code Subagents: eigene Kontexte und Toolrechte.
- AgentDojo/OWASP: Agenten mit Tools brauchen robuste Sicherheitskontrollen.
- LLM-as-Judge-Forschung: Bewertungsmodelle benötigen Reliability-Design.

### 5.2 Antithese

Das Repository erzeugt selbst einen Teil der Komplexität, die es auditieren will:

- viele Skills,
- viele Commands,
- lange SKILL-Dateien,
- komplexe Rubrics,
- mehrere Apply-Pfade,
- mehrere Evidence-Dokumente,
- zahlreiche Low-Evidence-Features.

Damit besteht das Risiko einer **Scheinpräzision**: Viele Rubric-Items und Reports wirken wissenschaftlich exakt, obwohl manche Entscheidungen lokale Heuristiken sind.

### 5.3 Synthese

Die korrekte Optimierung ist keine Reduktion auf einfache Prompts, sondern eine **geschichtete Architektur**:

1. Runtime-Skills kurz halten.
2. Komplexität in Referenzen, Schemas, Tests und Skripte verschieben.
3. Jede Rubric-Entscheidung evidenzklassifizieren.
4. Apply-Flows nur bei hoher Evidenz und geringer Änderungstiefe automatisieren.
5. Low-Evidence-Bereiche als experimentell führen.
6. Qualität empirisch messen, nicht nur argumentativ begründen.

---

## 6. Gesamtbewertung

| Bereich | Urteil | Evidenzstatus | Hauptbefund | Hauptrisiko | Priorität |
|---|---:|---|---|---|---:|
| Skills | B+ | Engineering guidance | fachlich stark, aber runtime-lastig | Kontext-/Constraint-Bloat | P1 |
| Agents | A- | Product-primary + supported inference | gute Perspektiventrennung | Rollenbias, Modellstärke, Korrelation | P2 |
| Hooks | A- | Product-primary + Security-standard | richtige Kontrollschicht | Log-Noise, Datenschutz, Policy-Lücken | P1 |
| Rules/References | B+ | gemischt | gute Verträge | Rubric-Bloat, Drift | P1 |
| Evidence Layer | A- | repo-intern stark | reflektierte Claim-Klassen | noch nicht Claim-by-Claim in Runtime | P0 |
| Research Results | B+ | heterogen | breite Themenabdeckung | ungleiche Tiefe, Preprint-Überdehnung | P0 |
| Apply-Flows | B | Engineering guidance | nützlich | automatische Änderungen auf schwacher Evidenz | P1 |
| Evaluation | C+ | Low-evidence gap | Ansätze vorhanden | keine robuste Eigenvalidierung | P0 |

---

## 7. Audit der Skills

### 7.1 Positiver Befund

Die Skills modellieren Review als Prozess, nicht als Einzelprompt. Das ist richtig. Ein Review-System braucht:

- definierte Eingaben,
- definierte Bewertungskriterien,
- definierte Ausgaben,
- Fehlerbehandlung,
- Nachvollziehbarkeit,
- Wiederholbarkeit,
- Validierungsschritte.

Das Repo setzt genau diese Struktur an. Die README beschreibt Review-, Apply-, Maintain-, Develop- und Discovery-Kommandos. Das ist für ein Claude-Code-Plugin mit Review-/Audit-Ziel fachlich angemessen.

### 7.2 Problem

Mehrere Skills scheinen zu viel Orchestrierungslogik direkt im Runtime-Pfad zu tragen. Das widerspricht teilweise dem Prinzip Progressive Disclosure: Der Hauptskill sollte nicht alle Details, Ausnahmen und Unterprotokolle permanent laden.

### 7.3 Wissenschaftliche Bewertung

Anthropic beschreibt Kontext als endliche Ressource und Agent Skills als progressive, gestuft geladene Wissenspakete. AGENTIF zeigt zugleich, dass Modelle mit langen, constraint-reichen agentischen Instruktionen Schwierigkeiten haben. Daraus folgt für dieses Repo: Kürzere Runtime-Skills sind nicht nur schöner, sondern zuverlässiger.

### 7.4 Empfehlung

**Change Request S1: Runtime-Skills entkernen.**

Zielstruktur:

```text
skills/<name>/SKILL.md
  - Ziel
  - Trigger
  - Minimalworkflow
  - harte Verbote / Allowances
  - Outputvertrag
  - Links auf Referenzen

skills/<name>/references/*.md
  - Rubric
  - Evaluation Guide
  - Boundary Examples
  - Failure Modes
  - Evidence Contract

scripts/ oder src/review_claude_config/
  - deterministische Checks
  - Merge
  - Report Validation
  - Token Budget
  - Hook Validation
```

**Priorität:** P1  
**Evidenzklasse:** Engineering guidance  
**Inferenztyp:** supported inference  
**Validierung:** Vorher/Nachher-Messung von Tokenverbrauch, Task Completion, Review-Vollständigkeit und Inter-Run-Stabilität.

### 7.5 Konkrete Annahmen, die nicht als bewiesen gelten dürfen

- Eine fixe maximale Zeilenzahl für SKILL.md ist kein wissenschaftliches Ergebnis.
- Die Zielgröße 150–250 Zeilen ist ein Repo Default, kein Proven Result.
- Kürzere Skills sind nur dann besser, wenn die nötige Information weiterhin bei Bedarf zuverlässig abrufbar ist.

---

## 8. Audit der Agents

### 8.1 Positiver Befund

Die Perspektiv-Agenten Clarity, Correctness und Integration sind inhaltlich sinnvoll. Claude Code Subagents sind offiziell für spezialisierte Aufgaben mit eigenem Kontext und spezifischen Toolrechten vorgesehen. Das Repo nutzt diese Funktion semantisch korrekt.

### 8.2 Wissenschaftliche Bewertung

Multi-Perspective-Review kann helfen, unterschiedliche Fehlerklassen sichtbar zu machen. Es ist jedoch kein automatischer Beweis für höhere Qualität. Entscheidend sind:

- Unabhängigkeit der Perspektiven,
- niedrige Fehlerkorrelation,
- klare Rollenabgrenzung,
- belastbare Merge-Regeln,
- Evaluation gegen Golden Cases.

### 8.3 Problem

Es ist unklar, ob die Agenten ausreichend unabhängig arbeiten. Wenn alle Agenten denselben Basiskontext und dieselbe überlange Rubric bekommen, droht gemeinsame Fehlkalibrierung.

### 8.4 Empfehlung

**Change Request A1: Agent-Rollen stärker entkoppeln.**

- Clarity-Agent: nur Verständlichkeit, Reihenfolge, Ambiguität, Preconditions.
- Correctness-Agent: nur inhaltliche Korrektheit, Completeness, falsche Annahmen.
- Integration-Agent: nur Toolrechte, Dependencies, Hook-/Command-Komposition, Security Surface.
- Optional: Skeptic-Agent zur False-Positive-Reduktion.

**Change Request A2: Model-Routing risikoabhängig machen.**

- einfache Clarity-Prüfung: günstiges Modell ausreichend.
- Correctness/Integration bei Write/Bash/WebFetch/MCP/Apply: stärkeres Modell.
- Safety-/Injection-Fälle: stärkstes verfügbares Modell oder menschliche Freigabe.

**Evidenzklasse:** Product-primary für Subagent-Eignung; Engineering guidance für Routing.  
**Validierung:** Pro Agent Precision, Recall, unique useful findings, false-positive rate.

---

## 9. Audit der Hooks

### 9.1 Positiver Befund

Die Hook-Architektur ist fachlich richtig. Hooks sind die richtige Ebene für deterministische Regeln, da Claude Code sie als automatisch ausgeführte Lifecycle-Kommandos definiert. Sie sind geeigneter als Prompt-Instruktionen, wenn eine Aktion jedes Mal passieren muss.

### 9.2 Sicherheitsbewertung

OWASP und AgentDojo stützen die Annahme, dass toolfähige Agenten besondere Sicherheitskontrollen benötigen. Hooks können dabei helfen, aber sie sind kein vollständiges Security-Modell.

### 9.3 Risiken

1. **Log-Noise:** Zu viele Audit-Hooks können relevante Signale verdecken.
2. **Sensitive Data:** Tool-Logs können Pfade, Inhalte oder Metadaten enthalten.
3. **Policy Drift:** Hook-Regeln müssen mit Skill- und Apply-Regeln synchron bleiben.
4. **False Blocking:** Harte Gates können legitime Änderungen verhindern.
5. **Host-Abhängigkeit:** Write-Approval- und Hook-Verhalten kann von Claude-Code-Host, Settings und Permissions abhängen.

### 9.4 Empfehlung

**Change Request H1: Hook Threat Model ergänzen.**

Dokumentieren:

- Welche Hooks blockieren?
- Welche Hooks loggen nur?
- Welche Hooks dürfen Daten persistieren?
- Welche Daten werden redacted?
- Wie lange werden Logs gespeichert?
- Welche Events sind security-critical?
- Welche Regeln gelten für reviewed artifacts als untrusted input?

**Change Request H2: Hook-Signal klassifizieren.**

```yaml
hook_event:
  class: block | warn | observe | summarize
  risk: low | medium | high
  data_sensitivity: none | metadata | content | secret-risk
  retention: none | session | rolling | persistent
  owner: maintainer | user | plugin
```

**Evidenzklasse:** Product-primary + Security-standard.  
**Validierung:** Hook false-block rate, missed-policy rate, log-size-per-run, security-event recall.

---

## 10. Audit von Rules, Rubrics und References

### 10.1 Positiver Befund

Das Repo besitzt ungewöhnlich starke Reference-Disziplin. Besonders positiv:

- Evidence Contract,
- Review Report Contract,
- Source Quality Criteria,
- Engineering Baseline,
- Dimension Evidence Coverage,
- Scientific Research Dossier,
- Evidence Maintenance Guide.

Diese Struktur ist für ein Meta-Review-System angemessen.

### 10.2 Problem

Rubrics können Qualität erhöhen, aber auch Scheinpräzision erzeugen. Wenn viele Items nicht empirisch validiert sind, wirkt die Bewertung genauer als sie ist.

### 10.3 Empfehlung

**Change Request R1: Jede Rubric-Zeile bekommt Evidence-Metadaten.**

```yaml
rubric_item:
  id: GA-3
  dimension: Goal Alignment
  evidence_class: Engineering guidance | Repo default | Low-evidence area | Proven result
  source_refs:
    - url_or_file
  inference_type: direct_source | supported_inference | heuristic | hypothesis
  auto_fail_allowed: true | false
  auto_apply_allowed: true | false
  reviewer_notes_required: true | false
```

**Change Request R2: Rubric-Bloat aktiv begrenzen.**

Jedes Item muss eine Frage beantworten:

1. Findet dieses Item Fehler, die andere Items nicht finden?
2. Hat es eine messbare False-Positive-Rate?
3. Ist es für Apply-Entscheidungen relevant?
4. Ist es evidenzgestützt oder nur lokal nützlich?

Items ohne messbaren Zusatznutzen sollten zusammengeführt, downgraded oder als advisory markiert werden.

**Evidenzklasse:** Engineering guidance / Repo default.  
**Validierung:** Ablation Study pro Rubric-Item-Gruppe.

---

## 11. Audit des Research-/Evidence-Layers

### 11.1 Positiver Befund

Das Repo hat bereits eine reflektierte Evidence-Struktur. Das Scientific Research Dossier definiert Tier-1-/Tier-2-/Tier-3-Quellen und benennt Low-Evidence-Zonen. Der Evidence-Maintenance-Guide verlangt kanonische Klassen und warnt vor Überdehnung schwacher Claims. Die Dimension Evidence Coverage Matrix führt pro Dimension Abdeckung, Quellen, grounded items und bekannte Lücken.

Das ist methodisch stark und für ein Open-Source-LLM-Agenten-Repo ungewöhnlich reif.

### 11.2 Kritischer Befund

Die Research Results sind breit, aber nicht gleichmäßig tief. Die eigene Matrix zeigt bereits:

- Metadata ist nur „Adequate“.
- Goal Alignment hat trotz hohem Gewicht historisch eine schmale Evidenzbasis.
- Skill-gap Detection bleibt Low-Evidence.
- Primitive derivation bleibt Low-Evidence.
- Exact token thresholds sind Repo Defaults.
- Command naming bleibt Low-to-medium evidence.

### 11.3 Externe Coverage-Prüfung

Aus Sicht eines wissenschaftlichen Audits fehlen oder sind zu schwach operationalisiert:

| Themenfeld | Status | Bewertung | Empfehlung |
|---|---|---|---|
| Context Engineering | gut abgedeckt | stark | weiter konsolidieren |
| Skill Progressive Disclosure | gut abgedeckt | stark | Runtime-Skills kürzen |
| Tool Safety / Prompt Injection | gut abgedeckt | stark | Meta-review threat model ergänzen |
| LLM-as-Judge Reliability | teilweise | mittel | Golden Dataset + Judge Calibration |
| Human-in-the-loop Governance | schwach | Lücke | Apply-Risk-Policy ergänzen |
| Evaluation Methodology | schwach-mittel | P0-Lücke | Evals formalisieren |
| Cost/Latency/Token Economics | schwach | Lücke | Metriken in Reports |
| Longitudinal Drift | schwach | Lücke | Trend-/Drift-Report |
| External Validity | schwach | Lücke | Fremdrepos testen |
| Ablation Studies | schwach | Lücke | Agent/Rubric/Hook ablatieren |
| Data Governance / Privacy | mittel | Lücke | Audit-log policy |
| Supply Chain for plugin install/update | mittel | Lücke | plugin update/rollback risks präzisieren |

### 11.4 Empfehlung

**Change Request E1: Claim-Evidence-Matrix einführen.**

Zentrale Claims aus Docs, Rubrics und Research-Dossier sollten maschinenlesbar erfasst werden:

```yaml
claim_id: CE-CLAIM-001
claim: Focused context management improves agent reliability.
location:
  - docs/scientific-research-dossier.md
  - references/engineering-baseline.md
source_refs:
  - https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
evidence_class: Engineering guidance
inference_type: supported_inference
repo_use: token-budgeting, progressive-disclosure, runtime-skill-trimming
limitations:
  - not a direct benchmark of this repository
last_verified: 2026-05-02
```

**Change Request E2: Research Results nicht nur sammeln, sondern operationalisieren.**

Für jede Research-Datei:

```yaml
operationalized_in:
  - rubric item
  - hook
  - skill rule
  - eval case
  - no current operationalization
```

Research ohne Operationalisierung ist nicht wertlos, aber sollte als Hintergrundwissen markiert werden.

---

## 12. Audit der Apply-Flows

### 12.1 Positiver Befund

Apply-Flows sind nützlich, weil sie Review-Findings in konkrete Verbesserungen übersetzen. Das ist produktiv und passt zum Repo-Ziel.

### 12.2 Risiko

Apply-Flows sind der gefährlichste Teil des Systems, weil hier LLM-Interpretationen zu Dateimutationen werden. Risiken:

- falsches Finding wird angewandt,
- semantische Intention des Autors wird verändert,
- Rubric-Overfitting,
- Prompt Injection aus reviewed artifact,
- ungeprüfte Mass Changes,
- stiller Drift von Skills/Rules.

### 12.3 Empfehlung

**Change Request P1: Apply-Risk-Matrix erzwingen.**

```yaml
finding:
  evidence_class: Proven result | Engineering guidance | Repo default | Low-evidence area
  confidence: high | medium | low
  change_type: formatting | structure | wording | policy | tool-permission | hook | apply-flow
  blast_radius: single-file | multi-file | runtime-behavior | security-sensitive
  auto_apply_allowed: true | false
  human_review_required: true | false
```

Automatisches Apply sollte nur erlaubt sein, wenn:

- `confidence = high`,
- `evidence_class != Low-evidence area`,
- `blast_radius` niedrig ist,
- keine Tool-/Permission-/Security-Semantik verändert wird,
- ein deterministischer Check existiert.

**Evidenzklasse:** supported inference aus Agent-Security und LLM-Judge-Reliability.

---

## 13. Empirische Validierung: Mindeststandard

Das Repo sollte erst dann von belastbarer Review-Qualität sprechen, wenn folgende Mindestmessungen existieren.

### 13.1 Golden Dataset

Mindestens:

- 20 gute Skills,
- 20 defekte Skills,
- 10 gute Agents,
- 10 defekte Agents,
- 10 gute Hook-Konfigurationen,
- 10 defekte Hook-Konfigurationen,
- 10 Rules/References mit bekannten Problemen.

Jeder Fall braucht:

```yaml
case_id:
artifact_type:
expected_findings:
acceptable_findings:
forbidden_findings:
severity_ground_truth:
source_of_truth:
reviewer_notes:
```

### 13.2 Metriken

| Metrik | Warum relevant |
|---|---|
| Precision pro Finding-Klasse | verhindert False-Positive-Flut |
| Recall pro Defektklasse | misst echte Fehlererkennung |
| Inter-Run-Stabilität | misst LLM-Varianz |
| Severity Calibration | verhindert über-/unterbewertete Findings |
| Time-to-review | Wirtschaftlichkeit |
| Tokens pro Review | Kontextökonomie |
| Tool Calls pro Review | Laufzeit-/Komplexitätsindikator |
| Apply Success Rate | Nutzen der Apply-Flows |
| Reopen/Regression Rate | Stabilität über Versionen |
| Human Override Rate | Vertrauen in Automatisierung |

### 13.3 Ablation Studies

Minimaler Ablation-Plan:

| Ablation | Frage |
|---|---|
| ohne Multi-Agent Review | Liefern Agents zusätzlichen Nutzen? |
| ohne Binary Evaluator | Wie viel Stabilität kommt aus deterministischen Checks? |
| ohne Domain Cache | Verbessert Research-Kontext echte Review-Qualität? |
| ohne Hooks | Welche Policies werden verpasst? |
| reduzierte Rubric | Ist die große Rubric besser als eine kompakte? |
| schwächeres Modell | Wo kippt Qualität? |
| ohne Apply-Automation | Wie hoch ist Apply-Mehrwert vs. Risiko? |

---

## 14. Coverage-Gap-Matrix

| Gap | Beschreibung | Evidenzstatus | Risiko | Priorität | Konkrete Maßnahme |
|---|---|---|---|---:|---|
| Golden Dataset | keine ausreichende Ground Truth | Low-evidence gap | Reviewqualität nicht belegbar | P0 | `tests/evals/golden/` erstellen |
| Claim-Evidence-Matrix | Claims nicht durchgängig maschinenlesbar | Repo gap | Scheinwissenschaftlichkeit | P0 | `docs/claim-evidence-matrix.yaml` |
| Runtime-Bloat | lange Skills/Prompts | supported inference | Constraint-Failure | P1 | Runtime-Skills kürzen |
| Apply-Governance | Änderungsrisiko nicht granular genug | supported inference | gefährliche Mutationen | P1 | Apply-Risk-Matrix |
| Meta-Review-Injection | reviewed artifacts als untrusted input nicht zentral genug | Security inference | Prompt Injection | P1 | Threat model ergänzen |
| LLM-Judge-Kalibrierung | keine robuste Judge-Evaluation | Survey-supported | unzuverlässige Scores | P0 | Judge eval suite |
| Ablation | Nutzen einzelner Komponenten unbewiesen | Low-evidence gap | Overengineering | P0 | ablation CI job |
| External Validity | nur Repo-intern plausibel | Low-evidence gap | schlechte Generalisierung | P2 | 3–5 Fremdrepos testen |
| Token Economics | Kosten/Nutzen unklar | Engineering gap | teure Reviews | P2 | Token-/runtime-Metriken |
| Hook Privacy | Auditdaten/Retention unklar | Security gap | Datenleck | P1 | retention/redaction policy |
| Research Operationalization | Forschung nicht immer in Rubrics/Evals übersetzt | Repo gap | Wissensdrift | P1 | operationalization field |

---

## 15. Priorisierte Roadmap

### P0: Wissenschaftliche Belastbarkeit herstellen

1. `docs/claim-evidence-matrix.yaml` einführen.
2. Golden Dataset erstellen.
3. LLM-Judge-Reliability messen.
4. Ablation Suite bauen.
5. Reports um Precision/Recall/Stability-Felder erweitern.

### P1: Runtime und Safety härten

1. Runtime-Skills kürzen.
2. Apply-Risk-Matrix einführen.
3. Hook Threat Model ergänzen.
4. Reviewed artifacts als untrusted input klassifizieren.
5. Rubric-Items mit Evidence-Metadaten versehen.

### P2: Wartbarkeit und Produktqualität verbessern

1. Command-Familien konsolidieren.
2. Research Operationalization Matrix einführen.
3. External Validity mit Fremdrepos testen.
4. Token-/Latency-Kosten reporten.
5. Drift-Monitoring über Versionen ergänzen.

---

## 16. Konkrete Änderungsvorschläge an den Repo-Autor

### 16.1 Neue Datei: `docs/claim-evidence-matrix.yaml`

Zweck: Jede zentrale Behauptung auditierbar machen.

Minimalfelder:

```yaml
claims:
  - id: CE-001
    claim: Focused context management matters for agent reliability.
    evidence_class: Engineering guidance
    inference_type: supported_inference
    source_refs:
      - https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
    repo_locations:
      - docs/scientific-research-dossier.md
      - skills/review-claude-config/references/engineering-baseline.md
    limitations:
      - Not directly benchmarked on this repository.
    last_verified: 2026-05-02
```

### 16.2 Neue Datei: `docs/meta-review-threat-model.md`

Inhalt:

- reviewed artifact is untrusted input,
- prompt injection through skill content,
- malicious hooks/rules,
- tool permission escalation,
- apply-flow mutation risk,
- report poisoning,
- stale evidence poisoning,
- mitigation controls.

### 16.3 Neue Datei: `docs/apply-risk-policy.md`

Inhalt:

- Auto-apply allowed cases,
- human-review-required cases,
- forbidden auto-apply cases,
- evidence thresholds,
- blast-radius thresholds,
- rollback expectations.

### 16.4 Neue Datei: `tests/evals/golden/README.md`

Inhalt:

- Golden case format,
- expected findings,
- forbidden findings,
- severity truth,
- evaluation command,
- pass/fail thresholds.

### 16.5 Update: `skills/*/SKILL.md`

Ziel:

- Runtime-Instruktionen kürzen,
- Detailprotokolle in References verschieben,
- Outputverträge maschinenlesbar machen,
- Low-Evidence-Funktionen sichtbar markieren.

### 16.6 Update: Rubric-Dateien

Jedes Rubric Item erhält:

```yaml
evidence_class:
inference_type:
auto_fail_allowed:
auto_apply_allowed:
source_refs:
```

---

## 17. Claim-by-Claim Validierung zentraler Audit-Aussagen

| Claim | Zulässige Formulierung | Evidenz | Klasse | Unsicherheit |
|---|---|---|---|---|
| Hooks sind für deterministische Kontrolle geeignet | Claude Code Hooks sind dafür vorgesehen, bestimmte Aktionen zuverlässig auszuführen | Claude Code Hooks Guide | Product-primary | Gilt für Claude Code, nicht für allgemeine Agenten |
| Lange agentische Instruktionen sind schwierig | Benchmarks zeigen Probleme bei langen, constraint-reichen agentischen Instruktionen | AGENTIF | Preprint evidence | Nicht direkt auf dieses Repo getestet |
| Skills sollten Progressive Disclosure nutzen | Anthropic beschreibt Progressive Disclosure als Kernprinzip von Agent Skills | Anthropic Agent Skills | Product-primary | Produktguidance, keine unabhängige Langzeitstudie |
| Subagents eignen sich für spezialisierte Aufgaben | Claude Code Subagents laufen in eigenem Kontext mit eigener Toolkonfiguration | Claude Code Docs | Product-primary | Kein Beweis für höhere Reviewqualität |
| Prompt Injection ist für Tool-Agenten relevant | Agenten mit Tools können durch untrusted data hijacked werden | AgentDojo, OWASP | Security/benchmark evidence | Abwehrwirkung repo-spezifischer Hooks muss gemessen werden |
| LLM-as-Judge braucht Reliability-Design | Surveys zeigen Bias-/Reliability-Probleme und Evaluationsbedarf | LLM-as-Judge Survey | Survey evidence | Konkrete Metriken repo-spezifisch wählen |
| Rubric-Bloat kann Scheinpräzision erzeugen | Viele Items ohne Validierung können Bewertungsgenauigkeit vortäuschen | supported inference | Heuristic | Muss über Ablation empirisch geprüft werden |
| Apply-Flows sind risikoreich | Mutierende Agentenpfade erhöhen Blast Radius | OWASP/AgentDojo + LLM-Judge concerns | supported inference | Repo-spezifische Fehlerrate unbekannt |
| Golden Dataset ist notwendig | Ohne Ground Truth keine belastbare Precision/Recall-Aussage | Evaluation methodology | Engineering guidance | Größe und Zusammensetzung sind Repo Defaults |

---

## 18. Kritische Selbstprüfung dieses Audits

### 18.1 AI-Professor-Perspektive

Die Architektur ist inhaltlich plausibel. Die größte wissenschaftliche Schwäche ist fehlende empirische Eigenvalidierung. Ohne Evals darf das Audit nur sagen: „gut begründetes Design“, nicht „nachgewiesen wirksam“.

### 18.2 Security-Reviewer-Perspektive

Das Repo erkennt viele Safety-Themen. Es sollte aber reviewed artifacts explizit als hostile/untrusted input behandeln und Apply-Flows stärker begrenzen. Hook-Logging braucht Datenschutz- und Retention-Regeln.

### 18.3 Software-Engineering-Perspektive

Das Repo ist funktionsreich, aber komplex. Konsolidierung, Schemas, Tests und eine stabilere Package-/CLI-Struktur würden Wartbarkeit erhöhen. Viele Skripte sind korrekt, sollten aber stärker als Produktmodule organisiert werden.

### 18.4 Wissenschaftsmethodische Perspektive

Das Repo hat eine gute Evidence-Kultur, aber braucht eine Claim-Evidence-Matrix und operationalisierte Evals. Research-Dateien dürfen nicht nur gesammelt werden; sie müssen auf Rubric Items, Hooks, Skills oder Tests gemappt werden.

### 18.5 Gegenhypothesen

Diese Hypothesen müssen aktiv getestet werden:

1. Multi-Agent-Review liefert keinen signifikanten Zusatznutzen gegenüber einem starken Einzelreview.
2. Die große Rubric erzeugt mehr False Positives als eine kompakte Rubric.
3. Domain Cache erhöht Kontextkosten stärker als Reviewqualität.
4. Apply-Flows überoptimieren Artefakte auf die Rubric.
5. Hooks erzeugen Audit-Noise statt wirksamer Kontrolle.
6. Das System generalisiert schlecht auf fremde Repos.

---

## 19. Schlussurteil

Das Repository ist fachlich gut und in Teilen außergewöhnlich reflektiert. Es befindet sich aber an einem Reifeübergang:

- Von **evidence-informed design**
- zu **empirically validated review system**.

Die nächste Optimierung sollte daher nicht lauten: „mehr Research, mehr Rubric, mehr Agents“. Sie sollte lauten:

> **Weniger ungeprüfte Komplexität, mehr messbare Validierung.**

Priorität haben:

1. Claim-Evidence-Matrix,
2. Golden Dataset,
3. Ablation Studies,
4. Judge Reliability Metrics,
5. Apply-Risk-Policy,
6. Meta-Review Threat Model,
7. Runtime-Skill-Reduktion.

Wenn diese Schritte umgesetzt werden, kann das Repo von einem sehr guten Claude-Code-Review-Plugin zu einem methodisch belastbaren Referenzsystem für agentische Konfigurationsreviews werden.

---

## Appendix A: Kurzfassung für Issues

### Issue 1: Add Claim-Evidence Matrix

Create `docs/claim-evidence-matrix.yaml` and map every central claim from dossier, baseline, rubric and runtime skills to source refs, evidence class, inference type, limitations and last verification date.

### Issue 2: Add Golden Eval Dataset

Create `tests/evals/golden/` with good/bad examples for skills, agents, hooks and rules. Measure precision, recall, severity calibration and inter-run stability.

### Issue 3: Add Meta-Review Threat Model

Document that reviewed artifacts are untrusted input. Cover injection through skills/rules/hooks/reports/research summaries and apply-flow mutation risks.

### Issue 4: Add Apply Risk Policy

Require evidence class, confidence, blast radius and mutation type before any finding can be auto-applied.

### Issue 5: Reduce Runtime Skill Bloat

Move long protocols from `SKILL.md` into references and scripts. Keep runtime instructions minimal and high-signal.

### Issue 6: Add Ablation Tests

Compare full system vs. reduced rubric, no multi-agent, no binary evaluator, no domain cache, no hooks and weaker model routing.

### Issue 7: Add Hook Data Governance

Classify hook events as block/warn/observe/summarize; define data sensitivity, redaction, retention and owner.

---

## Appendix B: Audit-Trail und Verifikationsgrenzen

### Geprüfte Repo-Dokumente

Die Bewertung stützt sich auf folgende öffentliche Repo-Artefakte als Untersuchungsgegenstand:

- `README.md`
- `docs/scientific-research-dossier.md`
- `docs/evidence-maintenance.md`
- `docs/dimension-evidence-coverage.md`
- `skills/` inklusive zentraler Runtime-Skills und Referenzstruktur
- `agents/` inklusive Review-Perspektiven
- `hooks/hooks.json`
- `research/` als Themeninventar und sekundäre interne Research-Sammlung
- zentrale deterministische Skripte unter `scripts/`

### Geprüfte externe Quellentypen

- offizielle Anthropic-/Claude-Code-Dokumentation für Claude-spezifische Funktionsaussagen,
- OWASP für agentische Security-Risiken und Kontrollprinzipien,
- arXiv-/Survey-Literatur nur mit expliziter Kennzeichnung als Preprint oder Survey,
- Repo-interne Research-Dateien nur als Untersuchungsgegenstand oder sekundäre Synthese, nicht als unabhängiger Beweis.

### Nicht geleistete empirische Verifikation

Dieses Audit hat keine Repo-Runs, keine wiederholten Claude-Code-Review-Läufe, keine Modell-A/B-Tests, keine Ablation Studies und keine Ground-Truth-Evaluation durchgeführt. Alle Aussagen zur erwarteten Wirksamkeit sind daher als `Engineering guidance`, `supported inference` oder `hypothesis` zu lesen, sofern kein direkter Messwert angegeben ist.

### Strenge Formulierungsregel

Zulässig:

> Die Architektur ist evidenzinformiert und methodisch plausibel.

Nicht zulässig:

> Die Architektur ist empirisch bewiesen wirksam.

## Appendix B: Quellenstatus

| Source type | Used as evidence? | Notes |
|---|---:|---|
| Official Anthropic / Claude Code docs | yes | Product-primary for Claude-specific behavior |
| OWASP | yes | Security-standard |
| arXiv preprints | yes, labeled | Not treated as peer-reviewed unless known |
| Surveys | yes, labeled | Used for field-level reliability concerns |
| Repo files | yes, as object of audit | Not external proof |
| Wikipedia | no | Excluded |
| Reddit/HN | no | Excluded |
| News articles | no | Excluded |
| Generic blogs | no | Excluded unless official foundation/vendor engineering note |

