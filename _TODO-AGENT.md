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

1. [x] **Migrate-Output überarbeiten: Alle Treffer ausgeben** – Verbose-Modus sinnvoll machen

   - **Context**: Aktuelle Logging-Patterns-Tabelle zeigt nur aggregierte Zahlen, aber Benutzer möchte alle konkreten Treffer sehen (z.B. alle 535 Print-Statements mit Datei/Zeile).

   - **Success criteria** (must be checked to finish task)

     - [x] Alle gefundenen Treffer werden ausgegeben (nicht nur aggregiert)
     - [x] Verbose-Modus zeigt detaillierte Liste mit file:line
     - [x] Output bleibt lesbar, aber vollständig

   - **Files to check/modify**

     - [x] `src/nicestlog/cli.py` (\_display_project_analysis)
     - [x] `src/nicestlog/project_analyzer.py` (\_analyze_complexity)

   - **Steps** (always action verbs, explicit order)

     - [x] Aktuelle Ausgabe analysieren (was wird aggregiert?)
     - [x] Funktion erweitern um detaillierte Treffer-Liste
     - [x] Verbose-Flag sinnvoll implementieren
     - [x] Testen mit verschiedenen Projekten

   - **Commit message hint**: "feat: show all matches in migrate output, improve verbose mode"

1. [x] **Migrate-Scan einschränken: Nur src/ Verzeichnis** – Weniger Rauschen in Ausgabe

   - **Context**: Migrate scannt derzeit das gesamte Projekt, inkl. examples/, tests/, docs/ - das erzeugt viel Rauschen mit Print-Statements in Demos. Sollte nur src/ scannen wie andere Kommandos.

   - **Success criteria** (must be checked to finish task)

     - [x] Migrate scannt nur src/ Verzeichnis
     - [x] Weniger irrelevante Print-Statements in Ausgabe
     - [x] Konsistent mit anderen Kommandos (check, etc.)
     - [x] Keine Regression in Funktionalität

   - **Files to check/modify**

     - [x] `src/nicestlog/cli.py` (migrate command implementation)
     - [x] `src/nicestlog/project_analyzer.py` (analyze_project function)

   - **Steps** (always action verbs, explicit order)

     - [x] Aktuelle Scan-Logik im migrate-Kommando finden
     - [x] Start-Verzeichnis von Projekt-Root auf src/ ändern
     - [x] Sicherstellen, dass .gitignore weiterhin respektiert wird
     - [x] Testen mit verbose-Modus - weniger Rauschen
     - [x] Vergleichen mit check-Kommando für Konsistenz

   - **Commit message hint**: "fix: migrate command should only scan src/ directory"

1. [x] **AST-Analyse verbessern: Nur echten Code finden** – Keine Strings/Kommentare

   - **Context**: Aktuelle Analyse findet Logging-Patterns in Strings und Kommentaren (z.B. "getLogger" in Listen, Docstrings), die nicht migriert werden müssen.

   - **Success criteria** (must be checked to finish task)

     - [x] Nur echte ausführbare Logging-Calls werden gefunden
     - [x] Strings und Kommentare werden ignoriert
     - [x] Weniger falsch-positive Treffer
     - [x] Genauere Migration-Empfehlungen

   - **Files to check/modify**

     - [x] `src/nicestlog/project_analyzer.py` (\_analyze_file_patterns)

   - **Steps** (always action verbs, explicit order)

     - [x] AST-Analyse verstehen (findet derzeit alles mit regex)
     - [x] Funktion ändern um echte AST-Knoten zu analysieren
     - [x] Strings und Kommentare ausschließen
     - [x] Testen mit verbose-Modus - nur echte Treffer
     - [x] Performance-Impact prüfen

   - **Commit message hint**: "fix: AST analysis should only find executable code, not strings/comments"

1. [x] **AST-Analyse: Logger-Typen korrekt unterscheiden** – Structlog vs Logging

   - **Context**: Aktuelle AST-Analyse erkennt viele structlog-Aufrufe fälschlicherweise als "logging" (z.B. log.info() wird als logging erkannt, obwohl es structlog ist).

   - **Success criteria** (must be checked to finish task)

     - [x] Structlog-Aufrufe werden korrekt als "structlog" erkannt
     - [x] Nur echte logging-Modul-Aufrufe werden als "logging" markiert
     - [x] Print-Statements bleiben als "print"
     - [x] Keine falsch-positiven Migration-Kandidaten

   - **Files to check/modify**

     - [x] `src/nicestlog/project_analyzer.py` (\_analyze_ast_tree, LoggingVisitor)

   - **Steps** (always action verbs, explicit order)

     - [x] Logger-Variablen tracken (welche Variable kommt von structlog.get_logger?)
     - [x] \_is_logging_call verbessern um Logger-Herkunft zu prüfen
     - [x] \_is_structlog_call erweitern um alle structlog-Aufrufe zu erkennen
     - [x] Testen mit verbose-Modus - korrekte Klassifizierung
     - [x] Performance sicherstellen

   - **Commit message hint**: "fix: AST analysis should correctly distinguish structlog from logging calls"

1. [x] **Check-Kommando: Output optimieren** – Weniger Rauschen für häufige Nutzung

   - **Context**: Check-Kommando produziert zu viel Output für normale Nutzung, vieles sollte nur im verbose-Modus erscheinen.

   - **Success criteria** (must be checked to finish task)

     - [x] Normale check-Ausgabe ist kompakt und übersichtlich
     - [x] Detaillierte Infos nur im --verbose Modus
     - [x] Wichtige Probleme werden trotzdem angezeigt
     - [x] Performance nicht beeinträchtigt

   - **Files to check/modify**

     - [x] `src/nicestlog/cli.py` (check command output functions)

   - **Steps** (always action verbs, explicit order)

     - [x] Aktuelle check-Ausgabe analysieren
     - [x] Output in normal/verbose Modi aufteilen
     - [x] Wichtige Probleme priorisieren
     - [x] Testen mit verschiedenen Szenarien
     - [x] Sicherstellen, dass nichts Wichtiges fehlt

   - **Commit message hint**: "feat: optimize check command output for frequent use"
