# Implementation TODO - nicestlog check text-only output per log.info statt print oder console.print

Beschreibe das Problem: nicestlog check verwendet print/console.print für Output, was nicht strukturiert ist. Stattdessen log.info verwenden für text-only, user-facing Output.

## Description

*(Scope, Motivation, Research, Related work – no checkboxes here!)*

- Problem statement: nicestlog check gibt Output mit print/console.print aus, was nicht in Logging integriert ist und nicht text-only ist (Farben, etc.).
- Why we want to solve it (value, impact): Konsistentes Logging, besser für Debugging und User-Feedback via Logs.
- Research / references: nicestlog verwendet rich/console für CLI-Output. log.info ist standard für Info-Messages.
- Constraints: Out-of-scope: Andere Befehle, nur check.

### Task Goal

- **Outcome we want**: nicestlog check verwendet log.info für alle user-facing Messages, text-only.
- **Success criteria**: Keine print/console.print in check-Code, Output ist text-only, funktioniert wie vorher.

______________________________________________________________________

## Tasks

*(Top-level numbered tasks with checkboxes, each with sub-structure – explicit, not vague)*

1. [x] **Finde alle print/console.print in nicestlog check Code**

   - **Context**: Identifiziere Stellen, wo Output erzeugt wird.

   - **Success criteria** (must be checked to finish task)

     - [x] Liste aller print/console.print in relevanten Dateien

   - **Files to check/modify**

     - [x] `src/nicestlog/cli.py` (check command)

   - **Steps** (always action verbs, explicit order)

     - [x] Grep nach print und console.print in src/nicestlog/
     - [x] Fokussiere auf check-related Code

   - **Commit message hint**: "Analyze print/console usage in nicestlog check"

1. [x] **Ersetze print/console.print durch log.info**

   - **Context**: Stelle sicher, Logging ist konfiguriert. nicestlog.init_logging ist schon in check-Funktion.

   - **Success criteria**

     - [x] Alle console.print in check-Funktion ersetzt durch log.info
     - [x] Rich markup entfernt für text-only Output
     - [x] Output bleibt informativ, aber ohne Farben

   - **Files to check/modify**

     - [x] `src/nicestlog/cli.py` (check-Funktion)

   - **Steps**

     - [x] Logger in check-Funktion einrichten: import logging; log = logging.getLogger(__name__)
     - [x] Jede console.print(...) ersetzen mit log.info(...), entferne [color] markup
     - [x] Behalte Emojis und Text, aber plain text
     - [x] Teste, dass Logging Output korrekt ist

   - **Commit message hint**: "Replace console.print with log.info in check command for text-only output"

1. [x] **Teste Änderungen**

   - **Context**: Stelle sicher, funktioniert. Zusätzlich: caplog in Tests funktioniert nicht mit structlog, daher Bridge zu standard logging hinzugefügt.

   - **Success criteria**

     - [x] uv run nicestlog check läuft ohne Fehler
     - [x] Output ist text-only für check-Messages
     - [x] Tests mit caplog funktionieren (Bridge zu logging)

   - **Files to check/modify**

     - [x] Tests anpassen falls nötig
     - [x] `src/nicestlog/core.py` (Bridge für caplog)

   - **Steps**

     - [x] Run check, vergleiche Output
     - [x] Run tests
     - [x] Bridge zu standard logging für caplog-Unterstützung

   - **Commit message hint**: "Test text-only output changes and add logging bridge for tests"
