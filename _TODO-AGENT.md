# Implementation TODO - Add linter rules section to logging_conventions.md

Beschreibe das Problem: Dokumentation fehlt Erklärung der spezifischen Linter-Regeln wie "Too little logging", redundante error=str(e), falsche Log-Levels. Füge Abschnitt hinzu, damit User wissen, wie richtig implementieren.

## Description

*(Scope, Motivation, Research, Related work – no checkboxes here!)*

- Problem statement: nicestlog check findet Issues, aber User wissen nicht, warum oder wie beheben.
- Why we want to solve it (value, impact): Bessere User-Experience, weniger Verwirrung.
- Research / references: Aus nicestlog check Output: Too little logging, redundant error params, wrong levels.
- Constraints: Nur docs/user_guide/logging_conventions.md ergänzen, keine Code-Änderungen.

### Task Goal

- **Outcome we want**: Neuer Abschnitt "Linter Rules and Common Issues" mit Erklärungen und Beispielen.
- **Success criteria**: Alle identifizierten Issues erklärt, mit korrekten und falschen Beispielen.

______________________________________________________________________

## Tasks

*(Top-level numbered tasks with checkboxes, each with sub-structure – explicit, not vague)*

1. [x] **Füge Abschnitt "Linter Rules and Common Issues" zu logging_conventions.md hinzu**

   - **Context**: Erkläre die Regeln, die nicestlog check erzwingt.

   - **Success criteria** (must be checked to finish task)

     - [x] Abschnitt hinzugefügt mit Erklärung von Too little logging
     - [x] Erklärung von redundant error=str(e) in log.exception()
     - [x] Erklärung von Log-Levels für interne Operationen
     - [x] Beispiele für korrekt und falsch

   - **Files to check/modify**

     - [x] docs/user_guide/logging_conventions.md

   - **Steps** (always action verbs, explicit order)

     - [x] Lies aktuelle logging_conventions.md
     - [x] Füge neuen Abschnitt nach "Best Practices" hinzu
     - [x] Schreibe Erklärungen mit Code-Beispielen
     - [x] Stelle sicher, Englisch und klar

   - **Commit message hint**: "docs: add linter rules section to logging conventions"
