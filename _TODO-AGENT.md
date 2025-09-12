# Performance-Optimierung: Migrate-Kommando beschleunigen

Das `uv run nicestlog migrate` dauert extrem lange, weil mehrere Funktionen ineffiziente Datei-Filterung verwenden. Ähnlich wie beim check Kommando werden .venv und andere ignorierte Verzeichnisse komplett durchsucht.

## Description

*(Scope, Motivation, Research, Related work – no checkboxes here!)*

- Problem statement: Mehrere migrate-Funktionen verwenden `directory.rglob("*.py")` ohne .gitignore-Filterung oder nur rudimentäre Filterung. Das führt zu Performance-Problemen bei großen .venv-Verzeichnissen.
- Why we want to solve it (value, impact): Performance-Verbesserung für migrate Kommando - soll nur relevante Source-Verzeichnisse scannen und ignorierte Verzeichnisse überspringen.
- Research / references: `migrate_directory_recursive` in cli.py, `migrate_directory` in assistant.py, `migrate_directory_with_handler` in cli.py.
- Constraints: Bestehende Funktionalität erhalten, nur Performance und Code-Deduplizierung.

### Task Goal

- **Outcome we want**: `migrate` Kommando läuft deutlich schneller, verwendet gemeinsame Datei-Filterung.
- **Success criteria**: Alle migrate-Funktionen verwenden optimierte Datei-Filterung, .venv wird nicht durchsucht.

______________________________________________________________________

## Tasks

*(Top-level numbered tasks with checkboxes, each with sub-structure – explicit, not vague)*

1. [x] **Gemeinsame Datei-Filterungs-Funktion erweitern** – Bestehende Funktion für migrate anpassen

   - **Context**: Die bestehende `filter_python_files` Funktion ist bereits optimiert, aber migrate-Funktionen verwenden sie nicht.

   - **Success criteria** (must be checked to finish task)

     - [x] `filter_python_files` wird von allen migrate-Funktionen verwendet
     - [x] Bestehende .gitignore-Logik wird genutzt
     - [x] Keine Regression in Funktionalität

   - **Files to check/modify**

     - [x] `src/nicestlog/cli.py`
     - [x] `src/nicestlog/assistant.py`

   - **Steps** (always action verbs, explicit order)

     - [x] Analysiere alle migrate-Funktionen mit rglob
     - [x] Ersetze rglob-Aufrufe mit filter_python_files
     - [x] Teste alle Migration-Typen
     - [x] Stelle sicher, dass .gitignore respektiert wird

   - **Commit message hint**: "perf: use shared file filtering in migrate functions"

1. [x] **Rudimentäre Filterung entfernen** – Ineffiziente Filter-Logik ersetzen

   - **Context**: Einige migrate-Funktionen haben rudimentäre Filterung wie `if any(part in {".venv", "venv", "__pycache__", ".git"} for part in py.parts)`, die besser durch .gitignore-Logik ersetzt werden kann.

   - **Success criteria** (must be checked to finish task)

     - [x] Keine rudimentäre Filterung mehr in migrate-Funktionen
     - [x] Vollständige .gitignore-Unterstützung
     - [x] Bessere Performance durch früheres Filtern

   - **Files to check/modify**

     - [x] `src/nicestlog/cli.py` (migrate_directory_with_handler)
     - [x] `src/nicestlog/assistant.py` (migrate_directory)

   - **Steps** (always action verbs, explicit order)

     - [x] Finde alle Stellen mit rudimentärer Filterung
     - [x] Ersetze durch gemeinsame filter_python_files Funktion
     - [x] Teste mit verschiedenen .gitignore-Konfigurationen
     - [x] Stelle sicher, dass alle ignorierten Dateien übersprungen werden

   - **Commit message hint**: "refactor: replace rudimentary filtering with proper gitignore handling"

1. [x] **Migrate-Performance testen** – Vorher/Nachher Vergleich

   - **Context**: Nach den Optimierungen sollte migrate deutlich schneller laufen.

   - **Success criteria** (must be checked to finish task)

     - [x] Migrate läuft schneller als vorher
     - [x] Alle Migration-Typen funktionieren korrekt
     - [x] Keine Regression in der Funktionalität

   - **Files to check/modify**

     - [x] Test-Scripts für Performance-Messung

   - **Steps** (always action verbs, explicit order)

     - [x] Erstelle Test-Szenario mit großem .venv
     - [x] Messe Performance vor und nach den Änderungen
     - [x] Teste alle Migration-Typen (print-to-structlog, cli-outputs, etc.)
     - [x] Dokumentiere Performance-Verbesserungen

   - **Commit message hint**: "test: verify migrate performance improvements"