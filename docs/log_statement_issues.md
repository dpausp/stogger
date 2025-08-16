# Log Statement Issues (aktuell erkannt)

Der AST-basierte Analyzer (`LogStatementAnalyzer`) erkennt aktuell folgende "log statement issues" in Python-Log-Aufrufen (z. B. `log.info(...)`, `log.debug(...)`, ...):

- missing_event_id
  - Es wurde keine Event-ID (erstes String-Argument) gefunden.
- event_id_not_dash_case (found: X)
  - Die Event-ID ist nicht im bevorzugten dash-case (z. B. snake_case, camelCase, PascalCase, invalid). Konfiguration: standardmäßig wird dash-case bevorzugt.
- single_string_argument
  - Es gibt genau ein (String-)Argument und weder Keyword-Argumente noch Magic-Args. Anti-Pattern: fehlende strukturierte Daten.
- fstring_in_event_id
  - Die Event-ID enthält `{` oder `}` (f-String/Template in der ID).
- debug_with_replace_msg
  - `log.debug(...)` wird zusammen mit `_replace_msg` verwendet (meist nicht erforderlich).
- too_many_kwargs (n>7)
  - Es gibt mehr als 7 normale Keyword-Argumente (ohne Magic-Args): zu komplex/umfangreich.
- no_structured_data
  - Es ist eine Event-ID vorhanden, aber keine Keyword-Argumente und kein `_replace_msg` – es fehlen strukturierte Daten.
- debug_for_error_event
  - `debug`-Level wird für Event-IDs verwendet, die auf Fehler hindeuten (beinhaltet Wörter wie "error", "fail", "critical", "fatal").
- error_level_for_info_event
  - `error`/`critical`-Level, obwohl die Event-ID eher nach Info/Debug aussieht (beinhaltet "debug", "trace", "info").
- potential_secret_leak (key)
  - Ein Keyword-Name wirkt sensibel (z. B. `password`, `secret`, `token`, `api_key`, `private_key`, ...). Hinweis auf mögliche Geheimnis-/Credential-Leaks.
- event_id_too_long (len>50)
  - Die Event-ID ist länger als 50 Zeichen.

Weitere Details:
- Magic-Args, die erkannt werden: `_replace_msg`, `exc_info`, `_structured`, `_level`, `_name`.
- Metriken wie `dash_case_violations`, `single_string_args` und `magic_args_usage` werden zusätzlich erhoben.

Diese Liste spiegelt den aktuellen Stand im Analyzer (`src/nicestlog/log_statement_analyzer.py`) wider.
