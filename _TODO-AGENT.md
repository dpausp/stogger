# Pure Log Statement Analysis with AST

Task goal
- AST tools sollen NUR Log-Statements analysieren: log.info(), logger.error(), etc.
- Imports und Type Hints checken um echte Logger zu identifizieren (z.B. structlog.get_logger())
- Nur die direkten Aufrufe von Logging-Statements zählen und analysieren
- Keine Funktionsanalyse, keine allgemeine Parameter-Analyse
- Nur: log.info(blah...) → analysiere die Argumente von diesem Call

Success criteria
- AST erkennt echte Logger durch Import-Analyse (structlog, logging, etc.)
- Nur tatsächliche Log-Statement-Calls werden analysiert
- Keine False Positives bei normalen Funktionen
- Type Hints werden berücksichtigt zur Logger-Erkennung

Out-of-scope for this task
- Funktionsanalyse jeder Art
- Allgemeine Code-Komplexität
- Parameter-Analyse von Nicht-Logging-Funktionen
- Architektur-Umschreibung

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)
- **Dogfooding**: Regelmäßig `uv run python -m nicestlog check` auf eigenem Code ausführen um zu validieren dass Änderungen Sinn ergeben

Prioritized work items (with checkboxes)

1) Understand current AST log detection
   - Context: Wie erkennt das System aktuell Log-Statements vs normale Funktionen?
   - Files to check/modify:
     - src/nicestlog/log_statement_analyzer.py
     - src/nicestlog/advanced_assistant.py
   - Steps:
     - [x] Analyze current log detection logic
     - [x] Check how imports are handled (logging, structlog, etc.)
     - [x] See if type hints are considered
     - [x] Test current behavior with mixed code (logging + normal functions)
     - [x] Commit with message: "docs: analyze current log statement detection"

2) Improve Logger identification through imports
   - Context: AST soll imports scannen um echte Logger zu finden
   - Files to check/modify:
     - src/nicestlog/log_statement_analyzer.py
   - Steps:
     - [ ] Add import scanning for logging libraries (logging, structlog, loguru, etc.)
     - [ ] Track logger variable assignments (logger = structlog.get_logger())
     - [ ] Consider type hints for logger identification
     - [ ] Build whitelist of known logging patterns
     - [ ] Commit with message: "feat: improve logger identification through import analysis"

3) Filter out non-logging function calls
   - Context: Nur echte Log-Statements analysieren, alles andere ignorieren
   - Files to check/modify:
     - src/nicestlog/log_statement_analyzer.py
     - src/nicestlog/advanced_assistant.py
   - Steps:
     - [ ] Apply logger whitelist to filter function calls
     - [ ] Ignore calls that aren't on identified loggers
     - [ ] Test with mixed codebase (logging + business logic)
     - [ ] Ensure no false positives on normal functions
     - [ ] Commit with message: "feat: filter analysis to log statements only"

4) Test with real-world examples
   - Context: Validierung mit echtem Code der logging + normale Funktionen mischt
   - Files to check/modify:
     - Create test files with mixed content
   - Steps:
     - [ ] Create test file with structlog + normal functions
     - [ ] Create test file with stdlib logging + business logic
     - [ ] Run AST analysis and verify only log statements are flagged
     - [ ] Document expected vs actual behavior
     - [ ] Commit with message: "test: validate log-only analysis with mixed code"