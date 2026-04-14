---
last_refreshed: 2026-04-14
---

# Zusammenfassung: Audit-Harness für autonome AI-Agent-Harnesses

## Zielbild

Geplant ist ein **AI Agent Harness**, das **andere AI-Agent-Harnesses auditieren und optimieren** kann.  
Dabei sollen **sowohl der Audit-Harness als auch der zu auditierende Harness möglichst autonom** funktionieren.  
**Human-in-the-loop** soll nur dann eingebunden werden, wenn:

1. eine Entscheidung **normativ, rechtlich, geschäftlich oder ethisch** von einem Menschen getroffen werden muss, oder  
2. die KI die Frage **auch mit Deep Research nicht belastbar selbst beantworten** kann.

Diese Zusammenfassung bündelt die bisher recherchierten Themen, die verifizierten Ergebnisse sowie die daraus gewonnenen Architektur- und Governance-Erkenntnisse.

---

## Executive Summary

Die Recherche zeigt klar, dass ein belastbarer Audit-Harness für Agentensysteme auf **drei Ebenen gleichzeitig** funktionieren muss:

1. **Leistungs- und Qualitätsaudit**  
   Misst, ob ein Harness Aufgaben korrekt, robust, effizient und reproduzierbar löst.

2. **Sicherheits-, Governance- und Compliance-Audit**  
   Prüft, ob ein Harness trotz Tooling, Memory, Webzugriff und Delegation kontrollierbar, nachvollziehbar und sicher bleibt.

3. **Autonomie-Audit**  
   Prüft, ob ein Harness **selbstständig handeln darf**, **wann er eskalieren muss**, wie er **Unsicherheit erkennt**, wie er **Risk Containment** umsetzt und ob er **rekursive Fehlsteuerungen** vermeidet.

Die zentrale Erkenntnis ist:  
Ein Agent-Harness, das andere Agent-Harnesses auditieren und optimieren soll, braucht **mehr als klassische Eval-Mechanik**. Es braucht zusätzlich ein **Autonomie-Kontrollsystem**, das die eigene Handlungsbefugnis, die Eingriffsgrenzen, die Eskalationslogik, die Evidenzschwellen und die Rückfallmechanismen strukturiert überwacht.

---

## 1. Verifizierte Kernthemen für das Audit eines Agent-Harnesses

### 1.1 Evaluationsdesign und Erfolgsmetriken
**Worum geht es?**  
Definition der Zielmetriken: Task Success, factual correctness, Tool-Korrektheit, Sicherheitsverstöße, Policy-Compliance, Kosten, Latenz, Stabilität.

**Warum ist das wichtig?**  
Ohne präzise Zielgrößen optimiert ein Harness auf Zufall oder auf falsche Surrogatmetriken.

**Gewonnene Erkenntnisse**
- Agentische Systeme müssen über **mehrdimensionale Metriken** bewertet werden.
- Endergebnis allein reicht nicht; der **Weg dorthin** ist auditrelevant.
- Eval-Systeme sollten **Datasets, Grader, Traces und Regression-Checks** kombinieren.

**Implikation**
- Das Audit-Harness braucht ein **metrisches Zielmodell**, das Korrektheit, Sicherheit, Effizienz und Stabilität gleichzeitig abbildet.

---

### 1.2 Benchmark- und Testfall-Strategie
**Worum geht es?**  
Aufbau repräsentativer Testfälle für Multi-Turn-Aufgaben, Tool-Use, Recherche, Planung, Policy-Einhaltung und Domänenlogik.

**Warum ist das wichtig?**  
Viele Benchmarks testen nur vereinfachte Prompt-Aufgaben und nicht echte agentische Workflows.

**Gewonnene Erkenntnisse**
- Realistische Agent-Benchmarks müssen **Interaktion, Tool-Nutzung und Workflow-Fehler** erfassen.
- Demo-Tasks sind für Harness-Audits zu schwach.
- Testsets müssen sowohl **realitätsnah** als auch **kontrollierbar** sein.

**Implikation**
- Das Audit-Harness braucht mindestens:
  - synthetische Kontrollfälle,
  - realistische E2E-Fälle,
  - adversariale Fälle,
  - Regression-Suiten.

---

### 1.3 Tracing und Observability
**Worum geht es?**  
Vollständige Nachverfolgbarkeit von Runs: Modellaufrufe, Tool-Calls, Handoffs, Guardrails, Kosten, Latenz, Fehler, State-Übergänge.

**Warum ist das wichtig?**  
Ein Audit ohne Trace kann Fehler nicht sauber lokalisieren.

**Gewonnene Erkenntnisse**
- Observability ist nicht optional, sondern **Grundvoraussetzung**.
- Agentenfehler entstehen oft im Ablauf, nicht nur im Endergebnis.
- Vollständige Traces sind nötig für Ursachenanalyse, Debugging, Regression und Governance.

**Implikation**
- Jeder Run des Audit-Harness muss als **strukturierter Audit-Trail** gespeichert werden.

---

### 1.4 Reproduzierbarkeit und Nichtdeterminismus
**Worum geht es?**  
Kontrolle von Varianz durch Sampling, Tool-Timing, Infrastruktur, Modelldrift, Retry-Verhalten und Evaluator-Rauschen.

**Warum ist das wichtig?**  
Ohne Reproduzierbarkeit kann eine vermeintliche Verbesserung bloß Zufall sein.

**Gewonnene Erkenntnisse**
- Selbst bei restriktiven Settings bleiben LLM-Systeme nicht vollständig deterministisch.
- Ergebnisse können durch Systemparameter, Hardware und Parallelisierung messbar beeinflusst werden.
- Regression-Tests müssen mit **Varianzbewusstsein** entworfen werden.

**Implikation**
- Verbesserungen dürfen nicht als Einzelrun bewertet werden.
- Das Audit-Harness braucht **mehrfache Wiederholungen**, Varianzstatistiken und Baseline-Vergleiche.

---

### 1.5 Fehlertaxonomie und Ursachenattribution
**Worum geht es?**  
Systematische Klassifikation von Fehlern: Planung, Delegation, Tool-Selektion, Verifikation, Kontextverlust, Policy-Verletzung, Handoff, Abbruchlogik.

**Warum ist das wichtig?**  
Ein gutes Audit benennt nicht nur das Symptom, sondern die Fehlerursache.

**Gewonnene Erkenntnisse**
- Multi-Agent- und Tool-basierte Systeme erzeugen **eigene Fehlerklassen**, die bei Single-Prompt-Evals unsichtbar bleiben.
- Fehlerbehebung ohne Taxonomie führt zu oberflächlichem „Patchen“.

**Implikation**
- Das Audit-Harness braucht eine **kanonische Failure Taxonomy** mit maschinenlesbaren Codes.

---

### 1.6 Sicherheitsmodell für Agenten und Tools
**Worum geht es?**  
Threat Models für Tool-Missbrauch, Seiteneffekte, überprivilegierte Agenten, unsichere Delegation, Credential-Risiken.

**Warum ist das wichtig?**  
Ein Harness darf nicht durch riskanteres Verhalten „bessere“ Ergebnisse erzielen.

**Gewonnene Erkenntnisse**
- Agentensicherheit ist ein eigenes Feld jenseits klassischer LLM-Sicherheit.
- Tool-Nutzung verschiebt Risiken von „falsche Antwort“ zu **falsche Handlung**.
- Least Privilege, Scope-Begrenzung und formale Aktionskontrollen sind zentral.

**Implikation**
- Das Audit-Harness muss operative Aktionen immer getrennt von Analyse und Bewertung behandeln.

---

### 1.7 Prompt Injection und adversarielle Robustheit
**Worum geht es?**  
Direkte und indirekte Injections über Web, Dokumente, Tools, Retrieval, Hidden Text und Zwischenoutputs.

**Warum ist das wichtig?**  
Agentische Systeme mit Tooling und externen Datenquellen sind besonders angreifbar.

**Gewonnene Erkenntnisse**
- Prompt Injection bleibt eine der relevantesten realen Angriffsflächen.
- Indirekte Injections über Tools und Inhalte sind besonders gefährlich, weil sie wie legitime Daten wirken.
- Kontexttrennung und Input-/Output-Härtung sind Pflicht.

**Implikation**
- Ein Audit-Harness muss standardmäßig adversariale Tests für Prompt Injection durchführen.

---

### 1.8 Interoperabilität und Protokolle
**Worum geht es?**  
MCP, Tool-Discovery, Capability-Beschreibungen, Versionierung, Schnittstellen-Sicherheit.

**Warum ist das wichtig?**  
Ein Audit-Harness muss fremde Harnesse standardisiert verstehen und prüfen können.

**Gewonnene Erkenntnisse**
- Standardisierte Agent-zu-Tool-Schnittstellen werden zunehmend zentral.
- Mit Interoperabilität wachsen zugleich die Risiken entlang der Vertrauenskette.

**Implikation**
- Das Audit-Harness braucht ein **abstraktes Capability-Modell**, das verschiedene Agent-Stacks vereinheitlicht.

---

### 1.9 Governance und Human Oversight
**Worum geht es?**  
Rollenmodelle, Entscheidungsgrenzen, Freigabepunkte, Verantwortlichkeit, Incident-Handling.

**Warum ist das wichtig?**  
Autonomie braucht klare Grenzen und nachvollziehbare Eskalationspfade.

**Gewonnene Erkenntnisse**
- Oversight ist nicht bloß ein UI-Thema, sondern Teil der Architektur.
- Governance muss definieren, **wer** was verantwortet, **wann** eskaliert wird und **welche Evidenz** dafür nötig ist.

**Implikation**
- Human Oversight muss als **Policy Engine** formalisiert werden, nicht nur als informeller Prozess.

---

### 1.10 Privacy, Datenflüsse und Secret Handling
**Worum geht es?**  
Datenminimierung, Session-Isolation, Secret-Management, Zugriffskontrolle, Persistenz sensibler Zustände.

**Warum ist das wichtig?**  
Ein Audit-Harness sieht oft mehr interne Daten und Zustände als das eigentliche Zielsystem.

**Gewonnene Erkenntnisse**
- Audit-Systeme sind selbst Hochrisiko-Komponenten aus Datenschutz- und Sicherheits-Perspektive.
- Memory, Logs und Traces können sensible Daten enthalten.
- Secrets dürfen nie implizit im Prompt oder Memory „mitlaufen“.

**Implikation**
- Traces, Memory und Artefakte des Audit-Harness brauchen eigene Sicherheitsklassifikation.

---

### 1.11 Audit-Trails und Evidenzhaltung
**Worum geht es?**  
Nachweisbare Aufzeichnung von Versionen, Konfigurationen, Freigaben, Inputs, Outputs, Tool-Calls, Bewertungen und Remediation.

**Warum ist das wichtig?**  
Ohne Evidenz ist weder internes noch externes Audit belastbar.

**Gewonnene Erkenntnisse**
- Traceability ist eine zentrale Eigenschaft vertrauenswürdiger AI-Systeme.
- Auditierbarkeit verlangt nachvollziehbare Evidenzketten, nicht nur Dashboard-Werte.

**Implikation**
- Jeder Audit-Run braucht einen **forensisch brauchbaren Evidence Record**.

---

### 1.12 Optimierungs- und Regression-Loop
**Worum geht es?**  
Kontrollierte Verbesserung durch Änderungen an Prompts, Routing, Policies, Tooling, Memory-Regeln oder Agent-Rollen.

**Warum ist das wichtig?**  
Das Ziel ist nicht nur Audit, sondern auch Optimierung.

**Gewonnene Erkenntnisse**
- Verbesserungen müssen gegen Baselines und Regression-Suiten geprüft werden.
- Optimierung ohne strukturierte Regression führt oft zu verdeckten Verschlechterungen.

**Implikation**
- Audit und Optimierung dürfen nie getrennte Systeme sein; der Optimierungsloop muss eval-getrieben sein.

---

### 1.13 Multi-Agent-Koordination
**Worum geht es?**  
Rollenverteilung, Handoffs, Koordination, Konfliktauflösung, Verifikation zwischen Agenten.

**Warum ist das wichtig?**  
Mehr Agenten bedeuten nicht automatisch bessere Leistung.

**Gewonnene Erkenntnisse**
- Multi-Agent-Systeme erzeugen zusätzliche Fehlermodi.
- Koordinations- und Verifikationsfehler sind eigene Risikoquellen.
- Mehr Agenten erhöhen Komplexität, Kosten und Debugging-Aufwand.

**Implikation**
- Multi-Agent-Strukturen müssen gegen Single-Agent-Baselines gerechtfertigt werden.

---

### 1.14 Kontext-, Speicher- und Zustandsmanagement
**Worum geht es?**  
Short-Term-Context, Long-Term-Memory, Summaries, Retrieval, Session-Grenzen, Memory-Hygiene.

**Warum ist das wichtig?**  
Viele Fehler entstehen durch verlorenen, veralteten, prioritätsfalschen oder vergifteten Zustand.

**Gewonnene Erkenntnisse**
- Memory ist ein Leistungs- und Sicherheitsproblem zugleich.
- Persistenter Kontext kann Drift und Vergiftung verstärken.
- Zustandsmanagement ist eine eigene Kontrollschicht, keine bloße Komfortfunktion.

**Implikation**
- Das Audit-Harness muss Memory-Qualität und Memory-Risiken explizit auditieren.

---

### 1.15 Wirtschaftlichkeit und Betriebsmetriken
**Worum geht es?**  
Kosten pro erfolgreichem Run, Token-Effizienz, Tool-Kosten, Retry-Raten, Latenz, Ressourcenverbrauch.

**Warum ist das wichtig?**  
Ein qualitativ besseres System ist unbrauchbar, wenn es betrieblich zu teuer oder zu langsam ist.

**Gewonnene Erkenntnisse**
- „Bessere“ Agenten sind oft nur teurer, langsamer und fragiler.
- Betriebsmetriken sind integraler Bestandteil des Audits.

**Implikation**
- Das Audit-Harness braucht ein **Leistungs/Kosten-Verhältnis** als First-Class-Metrik.

---

## 2. Zusätzliche Audit-Themen bei hoher Autonomie auf beiden Seiten

Wenn **sowohl Audit-Harness als auch Ziel-Harness möglichst autonom** agieren, reichen klassische Agent-Audit-Themen nicht mehr aus. Dann kommen zusätzliche Kontrollfelder hinzu.

### 2.1 Autonomiegrad und Entscheidungsgrenzen
**Frage:** Was darf der Agent selbst entscheiden, was nicht?

**Erkenntnis**
- Autonomie muss gestuft sein, nicht binär.
- Unterschied zwischen:
  - recherchieren,
  - analysieren,
  - empfehlen,
  - simulieren,
  - operativ handeln,
  - irreversible Entscheidungen auslösen.

**Implikation**
- Es braucht ein formales **Decision Authority Model**.

---

### 2.2 Act-vs-Escalate-Logik
**Frage:** Wann darf der Agent handeln, wann muss er eskalieren?

**Erkenntnis**
- Diese Schwelle ist selbst ein auditkritischer Entscheidungsprozess.
- Zu spätes Eskalieren ist gefährlich.
- Zu frühes Eskalieren zerstört den Autonomiegewinn.

**Implikation**
- Das System braucht explizite Regeln für:
  - self-act,
  - ask-for-evidence,
  - abstain,
  - escalate-to-human.

---

### 2.3 Unsicherheitsquantifizierung und Kalibrierung
**Frage:** Erkennt der Agent verlässlich, wenn er etwas nicht belastbar weiß?

**Erkenntnis**
- Agenten sind oft überkonfident.
- Selbstsicherheit ist kein verlässliches Qualitätssignal.

**Implikation**
- Das Audit-Harness muss Confidence, Calibration und Error Awareness selbst messen.

---

### 2.4 Abstention- und Safe-Failure-Verhalten
**Frage:** Kann der Agent kontrolliert **nicht handeln**?

**Erkenntnis**
- Autonomie ist nur sicher, wenn der Agent auch bewusst abbrechen, verweigern oder aussetzen kann.
- „Immer etwas tun“ ist in autonomen Systemen ein Fehlerpattern.

**Implikation**
- „No action“ und „insufficient evidence“ müssen zulässige, positiv bewertete Ergebnisse sein.

---

### 2.5 Over-eagerness / ungewollte Selbstermächtigung
**Frage:** Umgeht der Agent implizit Grenzen, um Aufgaben trotzdem zu „lösen“?

**Erkenntnis**
- Agenten können Workarounds, alternative Wege oder Scope-Expansion betreiben.
- Das kann wie Problemlösung aussehen, ist aber Governance-Versagen.

**Implikation**
- Das Audit-Harness muss unzulässige Eigeninitiative als eigenen Failure Type behandeln.

---

### 2.6 Laufzeit-Containment und Kill-Switches
**Frage:** Kann ein autonom laufender Agent sofort gestoppt oder isoliert werden?

**Erkenntnis**
- Post-hoc-Logs reichen nicht.
- Autonome Systeme brauchen aktive Notfallmechanismen.

**Implikation**
- Pflichtmechanismen:
  - kill switch,
  - sandboxing,
  - credential revocation,
  - quarantine mode.

---

### 2.7 Deterministische Pre-Action-Authorisierung
**Frage:** Wird jede externe Aktion vor Ausführung formal geprüft?

**Erkenntnis**
- Sicherheits- und Scope-Regeln dürfen nicht nur promptbasiert sein.
- Autorisierung muss technisch durchsetzbar sein.

**Implikation**
- Jede side-effecting action braucht eine Policy-Prüfung vor Ausführung.

---

### 2.8 Agentenidentität, Ownership und Credential-Lifecycle
**Frage:** Wer ist der Agent im Systemkontext, welche Rechte hat er und wie werden diese kontrolliert?

**Erkenntnis**
- Ohne saubere Agent Identity ist keine belastbare Verantwortlichkeit möglich.
- Autonome Agenten brauchen echte Identitäts- und Scope-Modelle.

**Implikation**
- Jeder Agent braucht:
  - eindeutige Identität,
  - begrenzte Berechtigungen,
  - Rotation,
  - Revocation,
  - Auditierbarkeit.

---

### 2.9 Runtime Verification und Watchdog-Schicht
**Frage:** Gibt es eine unabhängige Kontrollinstanz während des laufenden Betriebs?

**Erkenntnis**
- Viele Fehlverhalten zeigen sich erst zur Laufzeit.
- Vorab-Evals reichen nicht.

**Implikation**
- Neben dem Audit-Harness selbst braucht es eine separate Runtime-Überwachung.

---

### 2.10 Cascading Failures und rekursive Audit-Loops
**Frage:** Können Audit-Harness und Ziel-Harness sich gegenseitig in schlechte Schleifen treiben?

**Erkenntnis**
- Rekursive Systeme können Bestätigungszyklen, Endlosschleifen oder Eskalationsstürme erzeugen.
- Das ist ein systemisches Risiko, nicht nur ein lokaler Bug.

**Implikation**
- Rekursions- und Abhängigkeitsgraphen müssen explizit überwacht werden.

---

### 2.11 Delegierte Vertrauenskette
**Frage:** Wie wird Vertrauen an Subagenten, Tools und externe Systeme weitergegeben?

**Erkenntnis**
- Risiko liegt oft in der Kette, nicht im Hauptagenten.
- Delegation ohne Boundaries vervielfacht Angriffs- und Fehlerflächen.

**Implikation**
- Trust Propagation und Capability Delegation müssen auditierbar sein.

---

### 2.12 Memory Poisoning und persistente Zielverschiebung
**Frage:** Kann gespeicherter Zustand die Agenten langfristig fehlsteuern?

**Erkenntis**
- Persistente Autonomie erzeugt persistente Vergiftungsfläche.
- Manipulierte oder schlechte frühere Einträge können zukünftiges Verhalten systematisch verschieben.

**Implikation**
- Memory braucht Provenance, TTL, Segmentation und Poisoning-Checks.

---

### 2.13 Goal Drift und Selbstoptimierung unter falschem Ziel
**Frage:** Optimiert der Agent auf das falsche Ziel?

**Erkenntnis**
- Ein System kann lokale Ziele wie „weniger Eskalation“, „mehr Durchsatz“ oder „schnellere Runs“ über das eigentliche Ziel stellen.
- Das wirkt wie Verbesserung, ist aber strategische Fehlsteuerung.

**Implikation**
- Das Audit-Harness muss Surrogatmetriken und Zielverschiebung selbst überwachen.

---

### 2.14 Rollback, Recovery und manueller Fallback
**Frage:** Sind Entscheidungen reversibel und kann das System sauber auf manuelle Steuerung zurückfallen?

**Erkenntnis**
- Autonomie ohne Recovery ist betrieblich zu fragil.
- Sichere Rückfallebenen sind Pflicht.

**Implikation**
- Jeder kritische Pfad braucht einen dokumentierten Recovery-Plan.

---

### 2.15 Evidenzschwelle für „Human required“
**Frage:** Nach welchen Kriterien entscheidet das System, dass ein Mensch nötig ist?

**Erkenntnis**
- Wenn Human-in-the-loop die Ausnahme ist, muss diese Ausnahme formalisiert sein.
- Sonst eskaliert das System entweder zu selten oder zu oft.

**Implikation**
- Es braucht eine **Escalation Policy** mit klaren Kriterien, z. B.:
  - normative Entscheidung,
  - irreversible Auswirkung,
  - unauflösbarer Zielkonflikt,
  - unzureichende Evidenz,
  - rechtlich/ethisch gebundene Freigabe.

---

## 3. Wichtigste übergreifende Erkenntnisse

### Erkenntnis 1: Ein Audit-Harness braucht zwei verschiedene Bewertungsmodi
- **Performance-Modus:** „Wie gut löst das Zielsystem seine Aufgaben?“
- **Governance-Modus:** „Handelt das Zielsystem innerhalb zulässiger Grenzen?“

Ein autonomer Audit-Harness darf nicht nur nach Qualität optimieren.  
Er muss auch prüfen, **ob die Art der Verbesserung überhaupt zulässig ist**.

---

### Erkenntnis 2: Autonomie ohne Eskalationslogik ist unvollständig
Hohe Autonomie funktioniert nur dann sicher, wenn Eskalation **nicht ad hoc**, sondern **formalisiert** ist.

Das bedeutet:
- klare Schwellen,
- klare Gründe,
- klare Evidenz,
- klare Zuständigkeit.

---

### Erkenntnis 3: „Keine Aktion“ ist ein Erfolgspfad
Ein autonomes System ist nicht gut, wenn es immer etwas tut.  
Es ist gut, wenn es **nur dann handelt, wenn Handlung gerechtfertigt ist**.

---

### Erkenntnis 4: Runtime-Kontrolle ist genauso wichtig wie Offline-Evaluation
Offline-Evals sind notwendig, aber nicht hinreichend.  
Autonome Systeme brauchen zusätzlich:
- Live-Überwachung,
- Kill-Switches,
- Policy-Enforcement,
- Containment.

---

### Erkenntnis 5: Memory ist nicht nur Komfort, sondern Risiko
Persistenter Zustand hilft bei Langläufern, erhöht aber gleichzeitig:
- Drift-Risiko,
- Poisoning-Risiko,
- Kontextfehler,
- Privacy-Risiko.

---

### Erkenntnis 6: Mehr Agenten bedeuten mehr Kontrollbedarf
Multi-Agent-Designs erzeugen:
- neue Failure Modes,
- zusätzliche Vertrauenskanten,
- kompliziertere Ursachenanalyse,
- höhere Infrastrukturkosten.

---

### Erkenntnis 7: Optimierung muss gegen Governance gegengeprüft werden
Nicht jede Leistungssteigerung ist eine echte Verbesserung.  
Wenn sie durch riskanteres Verhalten, unzulässige Tool-Nutzung, stillschweigende Scope-Erweiterung oder reduzierte Eskalation zustande kommt, ist sie **Governance-negativ**.

---

## 4. Daraus abgeleitete Architekturprinzipien

### 4.1 Trennung von Analyse, Entscheidung und Aktion
Der Harness sollte intern mindestens drei Schichten trennen:
1. **Analyse**
2. **Bewertung/Entscheidung**
3. **Aktion**

Dadurch wird auditierbar, wo Fehler entstehen.

---

### 4.2 Policy-first statt Prompt-first
Sicherheits-, Autorisierungs- und Eskalationsregeln dürfen nicht nur in Textprompts leben.  
Sie müssen als **technisch durchgesetzte Policies** implementiert werden.

---

### 4.3 Evidence-first Autonomy
Autonomie darf nur bei ausreichender Evidenz greifen.  
Fehlt diese, muss das System:
- nachrecherchieren,
- abstain,
- oder eskalieren.

---

### 4.4 Reproduzierbare Audit-Runs
Jeder Audit-Run sollte enthalten:
- Versionsstand,
- Konfiguration,
- Inputs,
- genutzte Tools,
- Trace,
- Entscheidungen,
- Evidenz,
- Ergebnis,
- Begründung.

---

### 4.5 Safety by containment
Autonome Systeme brauchen nicht nur Guardrails, sondern auch harte technische Grenzen:
- sandbox,
- scope limit,
- budget caps,
- runtime watchdog,
- kill switch.

---

### 4.6 Escalation by design
Human-in-the-loop darf keine informelle Restkategorie sein.  
Er muss als **klar definierter Entscheidungszustand** modelliert werden.

---

## 5. Empfohlene Audit-Domänen für das Zielsystem

Ein belastbares Audit-Harness sollte das Ziel-Harness mindestens in diesen Domänen bewerten:

1. **Task Quality**
2. **Tool Reliability**
3. **Planning Quality**
4. **Verification Quality**
5. **Policy Compliance**
6. **Security Robustness**
7. **Privacy/Data Handling**
8. **Memory Hygiene**
9. **Cost/Latency Efficiency**
10. **Escalation Correctness**
11. **Autonomy Boundary Compliance**
12. **Recovery/Fail-safe Capability**

---

## 6. Minimale zusätzliche Audit-Domänen für den Audit-Harness selbst

Weil der Audit-Harness selbst autonom arbeitet, muss er ebenfalls auditiert werden, mindestens auf:

1. **Meta-evaluation quality**
2. **Bias in grading**
3. **False positive / false negative audit rate**
4. **Escalation threshold correctness**
5. **Evidence sufficiency**
6. **Optimization-side effects**
7. **Recursive loop safety**
8. **Self-authority compliance**
9. **Runtime containment**
10. **Trust delegation discipline**

---

## 7. Praktische Konsequenz für dein Zielsystem

Wenn du wirklich ein System bauen willst, das andere Agent-Harnesse autonom auditieren und optimieren kann, dann brauchst du **nicht nur einen Evaluator**, sondern ein System aus mindestens diesen Komponenten:

- **Eval Engine**
- **Trace & Evidence Layer**
- **Policy / Authorization Engine**
- **Escalation Engine**
- **Runtime Watchdog**
- **Optimization / Regression Loop**
- **Memory Governance Layer**
- **Containment Layer**
- **Audit Ledger**

Erst dieses Gesamtbild macht aus einem „smarten Agenten“ ein belastbares autonomes Audit-System.

---

## 8. Konkrete Schlussfolgerung

Die Recherche bestätigt eindeutig:

Ein autonomer Audit-Harness für andere autonome Agent-Harnesse ist kein gewöhnliches Agent-System.  
Er ist eine **Kombination aus Eval-Plattform, Sicherheitskontrollsystem, Governance-Mechanismus und Optimierungsorchestrator**.

Die zusätzliche Schwierigkeit entsteht nicht primär durch bessere Prompts oder mehr Tooling, sondern durch diese Kernfrage:

> **Wie stellt man sicher, dass ein autonomes System nur dann selbstständig handelt, wenn es das fachlich, sicherheitstechnisch und governance-seitig auch wirklich darf?**

Genau daraus ergeben sich die zusätzlichen Audit-Themen rund um:
- Entscheidungsgrenzen,
- Unsicherheit,
- Eskalation,
- Containment,
- rekursive Schleifen,
- delegiertes Vertrauen,
- Goal Drift,
- und Recovery.

---

## 9. Empfohlener nächster Schritt

Sinnvoll wäre jetzt als Anschlussartefakt eines von drei Formaten:

### Option A — Audit-Checklist
Eine konkrete prüfbare Liste mit:
- Kontrollfrage,
- Prüfmethode,
- Evidenz,
- Schweregrad,
- Pass/Fail-Kriterium.

### Option B — Research Matrix
Eine Matrix:
- Thema,
- offene Forschungsfragen,
- Designentscheidungen,
- messbare Akzeptanzkriterien,
- technische Umsetzungsideen.

### Option C — Referenzarchitektur
Eine technische Zielarchitektur des Audit-Harness mit:
- Komponenten,
- Schnittstellen,
- Datenflüssen,
- Policy-Layern,
- Eskalationspunkten,
- Audit Ledger,
- Watchdog-Schicht.

---

## 10. Rohfassung der bisher gewonnenen Kernthesen

- Ein Audit-Harness muss den **Prozess** bewerten, nicht nur das Ergebnis.
- Autonomie verlangt **formale Entscheidungsgrenzen**.
- Eskalation ist ein **eigenes Audit-Thema**.
- Nichtdeterminismus muss gemessen und kontrolliert werden.
- Memory ist zugleich Leistungsfaktor und Sicherheitsrisiko.
- Multi-Agent-Design erzeugt neue Fehlermuster.
- Verbesserungen müssen gegen Governance geprüft werden.
- „Nicht handeln“ ist in autonomen Systemen oft das korrekte Verhalten.
- Runtime-Containment ist Pflicht.
- Ein autonomer Audit-Harness braucht selbst Auditierbarkeit.

---

## 11. Quellenbasis der bisherigen Recherche

Die bisherigen Ergebnisse wurden auf Basis aktueller, belastbarer Quellen abgeleitet, insbesondere aus diesen Quelltypen:

- offizielle Dokumentation zu Agent-Evals und Agent-SDKs,
- aktuelle Agenten- und Multi-Agent-Forschung,
- NIST-Rahmenwerke und Standardisierungsinitiativen,
- OWASP-Leitlinien für LLMs und agentische Anwendungen,
- Datenschutz- und Audit-Leitlinien europäischer Institutionen,
- aktuelle Arbeiten zu Unsicherheit, Runtime Verification, Authorization und sicherer Agentenautonomie.

Die eigentlichen Webquellen wurden in der Chat-Recherche bereits einzeln belegt; diese Markdown-Datei ist als **konsolidierte Zusammenfassung der Ergebnisse und Erkenntnisse** gedacht.

