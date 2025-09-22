# Implementation TODO - Überprüfe nicestlog check Output und Dokumentation

Beschreibe das Problem: Führe uv run nicestlog check aus, analysiere was der Linter testet, und überprüfe ob alle getesteten Dinge in der Dokumentation gut erklärt sind, damit User das richtig implementieren können.

## Description

*(Scope, Motivation, Research, Related work – no checkboxes here!)*

- Problem statement: Möglicherweise sind nicht alle Linter-Regeln oder getesteten Dinge in der User-Dokumentation erklärt, was zu Verwirrung führt.
- Why we want to solve it (value, impact): Bessere User-Experience, damit User wissen, wie sie ihren Code richtig schreiben.
- Research / references: nicestlog check läuft Linter über Python-Dateien, prüft Logging-Konventionen.
- Constraints: Out-of-scope: Änderungen am Linter-Code, nur Dokumentation überprüfen.

### Task Goal

- **Outcome we want**: Vollständige Liste der vom Linter getesteten Dinge und Überprüfung, ob sie in docs/ dokumentiert sind.
- **Success criteria**: Alle getesteten Regeln sind in der Dokumentation erklärt, mit Beispielen.

______________________________________________________________________

## Tasks

*(Top-level numbered tasks with checkboxes, each with sub-structure – explicit, not vague)*

1. [ ] **Führe uv run nicestlog check aus und analysiere Output**

   - **Context**: Verstehe, was der Linter testet.

   - **Success criteria** (must be checked to finish task)

     - [ ] Output von nicestlog check gesammelt
     - [ ] Liste der getesteten Dinge extrahiert (z.B. Logging-Konventionen, Imports, etc.)

   - **Files to check/modify**

     - [ ] Keine Änderungen

   - **Steps** (always action verbs, explicit order)

     - [ ] Run uv run nicestlog check
     - [ ] Sammle die Ausgabe
     - [ ] Identifiziere alle gemeldeten Issues und Regeln

   - **Commit message hint**: "Analyze nicestlog check output for tested rules"

1. [ ] **Überprüfe Dokumentation auf Vollständigkeit**

   - **Context**: Stelle sicher, dass alle getesteten Dinge dokumentiert sind.

   - **Success criteria**

     - [ ] Alle getesteten Regeln in docs/ gefunden
     - [ ] Dokumentation enthält Beispiele und Erklärungen
     - [ ] User können daraus lernen, wie richtig implementieren

   - **Files to check/modify**

     - [ ] docs/user_guide/logging_conventions.md
     - [ ] docs/user_guide/best_practices.md
     - [ ] Andere relevante docs/

   - **Steps**

     - [ ] Lies relevante Dokumentationsdateien
     - [ ] Vergleiche mit der Liste der getesteten Dinge
     - [ ] Identifiziere fehlende Dokumentation
     - [ ] Vorschlage Ergänzungen falls nötig

   - **Commit message hint**: "Review documentation for linter-tested rules completeness"
