Die Agents haben viele Tokens verbraucht, weil sie die gesamte Codebase lesen mussten – wie Buchprüfer, die jeden Ordner im Aktenschrank durchblättern:
Hauptgründe:
Große Codebase – 70+ Controller, 39 Services, 66 Models, 100+ Blade-Views. Jeder Agent musste dutzende Dateien lesen um ein fundiertes Urteil abzugeben.
10 Agents parallel – Jeder hat unabhängig die gleichen Basis-Dateien gelesen (Models, Routes, Config). Das ist wie 10 Leute, die alle dasselbe Buch gleichzeitig lesen – 10x der Verbrauch.
Tool-Calls pro Agent: 50-75 – Jeder Read, Grep, Glob Aufruf kostet Tokens für Input + Output. Der Test-Coverage-Agent z.B. hat 67 Tool-Calls gemacht um alle Controller gegen alle Testdateien abzugleichen.
Token-Verteilung der erfolgreichen Agents:
Agent	Tokens	Tool-Calls
UI/UX Design	105K	62
Test Coverage	85K	67
API Design	70K	50
Tailwind CSS	66K	69
Die 6 die am Rate-Limit gescheitert sind, haben jeweils ~50-70 Tool-Calls gemacht bevor das Sonnet-Limit griff – also ähnlich viel gelesen, konnten aber den Report nicht mehr schreiben.
Nächstes Mal effizienter: Statt 10 generische Agents könnte man gezielter 3-4 mit spezifischen Dateipfaden losschicken, statt jeden Agent die ganze Codebase explorieren zu lassen.
