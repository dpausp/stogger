# Lessons Learned: Dogfooding `nicestlog check`

Status: Erfahrungsbericht und Leitfaden für Entwicklerinnen und Entwickler. Fokus: systematisches Vorgehen, sinnvolle Logging-Signale in Bibliothekscode, Vorher/Nachher-Beispiele.

## TL;DR
- Scopet den Check auf library-relevante Pfade (z. B. `src/…`) und schließt Tests/Docs/Beispiele aus.
- Interne Fortschrittsmeldungen gehören auf `log.debug`, nicht `log.info`.
- Fügt wenige, gezielte Debug-Logs an kritischen Pfaden hinzu (I/O, Auswahl/Ausführung von Transformationen, Fehlerpfade), statt “überall ein wenig”.
- Optional ein kompaktes `log.info`-Summary am Ende einer Operation – aber nur, wenn es sichtbare, user-relevante Effekte gab.

## 1. Ausgangslage und Ziele
Beim Dogfooding von `uv run nicestlog check` auf NicestLog war die Rohsicht sehr “laut”: Viele Fehler/Warnungen in Tests, Beispielen und Doku. Unser Ziel war ein präziseres Signal für den Bibliothekscode, ohne Nutzer-Noise.

## 2. Systematisches Vorgehen
1) Scoping – Fokus auf Library-Code
   - In `pyproject.toml` via `[tool.nicestlog].exclude` folgende Pfade ausgeschlossen:
     - `tests/**`, `docs/**`, `examples/**`
   - Ergebnis: Der Check fokussiert sich auf `src/nicestlog/…` und liefert ein verwertbares Signal.

2) Log-Level-Policy für Bibliotheken
   - Interne, rein technische Fortschrittslogs auf `debug` (z. B. "…-started", "…-completed", "…-matched").
   - `info` nur, wenn ein für Anwender relevantes Ereignis eintritt (z. B. es wurden tatsächlich Änderungen geschrieben, Migration abgeschlossen, wesentliche Metrik-Summary).

3) Zielgerichtete Debug-Logs
   - Statt pauschal Logs überall hinzuzufügen, identifizieren wir “kritische Pfade” und fügen dort strukturierte `log.debug`-Statements hinzu:
     - Vor und nach I/O (Datei lesen/schreiben, Backups anlegen)
     - Auswahl/Ausführung von Transformationen (Anzahl, Liste, Treffer ohne Transformer)
     - Erzeugung von Resultaten (Code-Unparse, Metriken)
     - Verzeichnisläufe (Dateiliste, Anzahl)
     - Fehlerpfade (Exceptions mit `error` loggen, inkl. Exception-Typ)

4) Iteratives Prüfen
   - Nach Änderungen: `uv run nicestlog check src/nicestlog` ausführen und nur die relevanten Module prüfen.
   - W3-Hinweise (Level-Missbrauch) zuerst beheben, dann E1/E2 gezielt verbessern.

## 3. Konkrete Anpassungen (Auszug)
- Linter-Konfiguration erweitert: `[tool.nicestlog].exclude` in `pyproject.toml` unterstützt und gesetzt (`tests/**`, `docs/**`, `examples/**`).
- `cli.py`: interne Abschlussmeldungen `info → debug`.
- `i18n.py`/`factory.py`: interne `info → debug`.
- `advanced_assistant.py`: mehrere interne Fortschritts-Logs `info → debug` und neue zielgerichtete `debug`-Logs eingefügt:
  - Datei-Pipeline: `read-file`, `apply-transformations`, `generate-code`, `write-backup`, `write-transformed`, `file-transformation-completed`
  - Pattern-Fluss: `pattern-matched`, `pattern-matched-no-transformer`, `node-transformed`
  - Verzeichnislauf: `directory-transformation-started`, `directory-files-selected`, `directory-transformation-completed`

## 4. Vorher/Nachher-Beispiele

### 4.1 Level-Alignment (vorher → nachher)
- Vorher (interner Abschluss als `info`):
  ```python
  log.info("config-wizard-completed")
  ```
- Nachher (intern → `debug`):
  ```python
  log.debug("config-wizard-completed")
  ```

### 4.2 Zielgerichtete Debug-Logs (neu)
- Vorher (kein Signal vor I/O):
  ```python
  # …
  original_content = file_path.read_text(encoding="utf-8")
  tree = ast.parse(original_content)
  # …
  ```
- Nachher (gezielter Kontext vor I/O):
  ```python
  log.debug("read-file", _replace_msg="📖 Reading and parsing file {file_path}", file_path=str(file_path))
  original_content = file_path.read_text(encoding="utf-8")
  tree = ast.parse(original_content)
  ```

- Vorher (ohne explizites Signal vor dem Unparse):
  ```python
  transformed_tree = transformer.transform(tree)
  transformed_content = ast.unparse(transformed_tree)
  ```
- Nachher (Explizites Signal):
  ```python
  log.debug("generate-code", _replace_msg="🧪 Generating code from transformed AST")
  transformed_content = ast.unparse(transformed_tree)
  ```

- Vorher (Schreiben ohne Kontext):
  ```python
  backup_path.write_text(original_content)
  file_path.write_text(transformed_content)
  ```
- Nachher (sichtbarer Schreibpfad):
  ```python
  log.debug("write-backup", _replace_msg="🗂️ Creating backup file for {file_path}", file_path=str(file_path))
  backup_path.write_text(original_content)
  log.debug("write-transformed", _replace_msg="✍️ Writing transformed content to {file_path}", file_path=str(file_path))
  file_path.write_text(transformed_content)
  ```

### 4.3 Pattern ohne Transformer (neu)
- Vorher: kein sichtbares Signal.
- Nachher:
  ```python
  log.debug(
      "pattern-matched-no-transformer",
      _replace_msg="ℹ️ Pattern '{pattern}' matched but has no transformer",
      pattern=pattern_name,
      line=getattr(node, "lineno", "unknown"),
      node_type=type(node).__name__,
  )
  ```

## 5. Empfehlungen für Bibliothekscode
- Benutzt `debug` großzügig für interne Schritte; `info` sparsam für sichtbare Ereignisse.
- Nutzt strukturierte Schlüssel (z. B. `file_path`, `pattern`, `duration`), damit Logs maschinenlesbar und filterbar sind.
- Definiert und nutzt eine kleine Menge stabiler Event-Namen (z. B. `file-analysis-started`, `apply-transformations`, …).
- Prüft regelmäßig mit `nicestlog check` (scoped), um Level-Fehlgriffe und Lücken zu erkennen.

## 6. Nächste Schritte
- Optional: INFO-Summary am Ende einer Operation, wenn Änderungen erfolgt sind (z. B. Anzahl Änderungen, Dauer).
- Weitere gezielte Uplifts in `interactive_transformer.py` und `live_editor.py` (State-Änderungen, Transformationen, Fehlersignale).
- Thresholds ggf. an Bibliotheksrealität anpassen (z. B. minimale Coverage/Quoten).
