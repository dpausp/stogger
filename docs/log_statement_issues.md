# Log Statement Issues (currently detected)

The AST-based analyzer (`LogStatementAnalyzer`) currently detects the following "log statement issues" in Python log calls (e.g., `log.info(...)`, `log.debug(...)`, ...):

- missing_event_id
    - No event ID (first string argument) found.
- event_id_not_dash_case (found: X)
    - Event ID is not in preferred dash-case (e.g., snake_case, camelCase, PascalCase, invalid). Configuration: prefers dash-case by default.
- single_string_argument
    - Exactly one (string) argument and neither keyword arguments nor magic args. Anti-pattern: missing structured data.
- fstring_in_event_id
    - Event ID contains `{` or `}` (f-string/template in the ID).
- debug_with_replace_msg
    - `log.debug(...)` used together with `_replace_msg` (usually not needed).
- too_many_kwargs (n>7)
    - More than 7 regular keyword arguments (excluding magic args): too complex/verbose.
- no_structured_data
    - Event ID present, but no keyword arguments and no `_replace_msg` — structured data missing.
- debug_for_error_event
    - `debug` level used for event IDs that sound like errors (contains words like "error", "fail", "critical", "fatal").
- error_level_for_info_event
    - `error`/`critical` level while event ID looks like info/debug (contains "debug", "trace", "info").
- potential_secret_leak (key)
    - Keyword name appears sensitive (e.g., `password`, `secret`, `token`, `api_key`, `private_key`, ...). Hint at possible secret/credential leaks.
- event_id_too_long (len>50)
    - Event ID is longer than 50 characters.

Further details:
- Magic args recognized: `_replace_msg`, `exc_info`, `_structured`, `_level`, `_name`. 
- Metrics like `dash_case_violations`, `single_string_args`, and `magic_args_usage` are also tracked.

This list reflects the current state of the analyzer (`src/nicestlog/log_statement_analyzer.py`).
